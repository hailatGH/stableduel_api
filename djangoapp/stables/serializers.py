from datetime import datetime
from django.core.cache import cache
from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Stable, Runner, get_stable_count, get_stable_scratched_count
from games.models import Game, Racecard
from datetime import datetime, timezone
from collections import defaultdict
from racecards.utils import get_full_race_time


User = get_user_model()

import logging
log = logging.getLogger()

class StableSerializer(serializers.ModelSerializer):
    runners = serializers.PrimaryKeyRelatedField(many=True, read_only=False, queryset=Runner.objects.all())
    user = serializers.PrimaryKeyRelatedField(read_only=False, queryset=User.objects.all(), default=serializers.CurrentUserDefault())
    state = serializers.SerializerMethodField()
    class Meta:
        model = Stable
        fields = (
            'id',
            'game',
            'user',
            'runners',
            'score',
            'rank',
            'is_valid_at_start',
            'scratch_limit_reached',
            'scratches_at_finish',
            'stable_count_at_finish',
            'is_submitted',
            'state',
            'entry_number',
            'created_at',
            'updated_at',
            
            'replaced_scratches_count'
        )

        read_only_fields = (
            'is_valid_at_start',
            'scratch_limit_reached',
            'scratches_at_finish',
            'stable_count_at_finish',
            'created_at',
            'updated_at',
            'score',
            'rank',
            'entry_number'
        )

    def get_state(self, obj):
        if (obj.game.game_state == Game.OPEN):
            return (Stable.NOT_STARTED_VALID  if self.isValid(obj) == True else Stable.NOT_STARTED_INVALID)
        elif (obj.game.game_state == Game.LIVE):
            if (obj.is_valid_at_start == False):
                return Stable.STARTED_DISQUALIFIED

            #This was copied from the iOS code but will never be called so I removed
            #if (self.isValid(obj) == False and obj.is_valid_at_start == False):
            #    return Stable.STARTED_DISQUALIFIED
            
            if (self.isComplete(obj) == True and self.hasScratchAndCanReplace(obj)):
                return Stable.STARTED_NEEDS_SCRATCH_REPLACEMENT
           
            if (self.isComplete(obj) == False and obj.is_valid_at_start == True):
                return Stable.STARTED_IS_REPLACING_SCRATCH

            if (self.isComplete(obj) == True):
                return (Stable.STARTED_DISQUALIFIED if obj.is_valid_at_start == False else Stable.STARTED_VALID)
                    
        elif (obj.game.game_state == Game.RESULTS_PENDING):
            return Stable.FINAL_RESULTS_PENDING if obj.is_valid_at_start == True else Stable.STARTED_DISQUALIFIED
        elif (obj.game.game_state == Game.FINISHED):
            if obj.is_valid_at_start == True and obj.scratch_limit_reached == False:
                return Stable.FINISHED
            else:
                return Stable.FINISHED_DISQUALIFIED
        elif (obj.game.game_state == Game.CANCELLED):
            return Stable.FINISHED if obj.is_valid_at_start == True else Stable.FINISHED_DISQUALIFIED

        return Stable.UNKNOWN


    def isValid(self, obj):
        return self.isComplete(obj) and get_stable_scratched_count(obj) <= 3
    
    def isComplete(self, obj):
        return self.numberOfEmptyRunners(obj) == 0 and self.remainingSalary(obj) >= 0

    def runnersSalaryTotal(self, obj): 
        salary = 0

        coupled_runners = defaultdict(list)
        for runner in obj.runners.all():
            if(runner.coupled == True):
                coupled_runners[runner.coupled_indicator].append(runner)
            else:
                salary = salary + runner.salary

        #Include the salary once for each set of coupled runners
        for coupled_indicator_value in coupled_runners:
            salary = salary + coupled_runners[coupled_indicator_value][0].salary
            
        return salary

    def remainingSalary(self, obj):
        return obj.game.salary_cap - self.runnersSalaryTotal(obj)
        
    def numberOfEmptyRunners(self, obj):
        return obj.game.runner_limit - get_stable_count(obj)
        
    def hasScratchAndCanReplace(self, obj):
        #make sure that the game still has a race left
        another_race_left = False
        
        for race in obj.game.racecard.races:
            race_date = datetime.strptime(race["adjusted_date"], "%Y-%m-%d")
            post_time = datetime.strptime(race["post_time"], '%I:%M%p')
            race_date_time = datetime.combine(race_date, post_time.time())
            if(race_date_time > datetime.now()):
                another_race_left = True
                break

        return self.isComplete(obj) and self.hasNonCoupledScratch(obj) and another_race_left
    
    def hasNonCoupledScratch(self, obj):
        hasNonCoupledScratch = False
        scratchedRunners = obj.runners.filter(scratched=True)

        coupled_runners = defaultdict(list)
        for runner in obj.runners.all():
            if(runner.coupled == True):
                coupled_runners[runner.coupled_indicator].append(runner)


        for scratchedRunner in scratchedRunners:
            foundUnscratchedPaired = False
            if(scratchedRunner.coupled == True):
                #Find the paired runners that aren't scratched
                for coupled_runner in coupled_runners[scratchedRunner.coupled_indicator]:
                    if(coupled_runner.scratched == False):
                        foundUnscratchedPaired = True

            if foundUnscratchedPaired == False:
                hasNonCoupledScratch = True

        return hasNonCoupledScratch

    def validate(self, data):
        user = data['user']
        game = data['game']
        runners = data['runners']

        if not self.instance:
            if game.started:
                raise serializers.ValidationError({'detail': 'Game has started. Additional stables cannot be created for this game'})
            if(game.stable_limit == -1):
                return data

            existing_stables = Stable.objects.filter(user=user, game=game).count()
            if(existing_stables + 1 > game.stable_limit):
                raise serializers.ValidationError({'detail': 'User has already has max stables for this game'})
        else:
            stable = self.instance
            stable_state = self.get_state(self.instance)
            if stable.is_valid_at_start == False:
                raise serializers.ValidationError({'detail': 'Cannot add runners to a stable after the game has started'})

            if stable.game.started and (stable_state not in [Stable.STARTED_NEEDS_SCRATCH_REPLACEMENT, Stable.STARTED_IS_REPLACING_SCRATCH]):
                raise serializers.ValidationError({'detail': 'Cannot modify runners for a stable after the game has started'})

        return data
    
    # Custom code to overide the update method of the serializer
    def update(self, instance, validated_data):
        # Check if replaced scratches count is more than allowed which is 3
        # replaced_scratches_count = Stable.objects.get(id=instance.id).replaced_scratches_count
        
        # Check if stable is submitted
        is_submitted = Stable.objects.get(id=instance.id).is_submitted
        
        if is_submitted:
            # if replaced_scratches_count >= 3:
                # raise serializers.ValidationError({'detail': 'Maximum replaced scratches count reached!'})
            
            # Getting racecard id from game
            racecard_id = Game.objects.get(id=validated_data.get("game").id).racecard.id
            races = Racecard.objects.get(id=racecard_id).races
            race_status = races[0]['status']
            race_date_time =  get_full_race_time(races[0])
            
            # Get list of current runners and incoming runners
            current_runners = sorted(list(instance.runners.values_list('id', flat=True)), reverse=False)
            incomming_runners = sorted([obj.id for obj in validated_data.get('runners')], reverse=False)
            
            # if len(current_runners) != len(incomming_runners):
            #     raise serializers.ValidationError({'detail': 'You can not add new runners!'})
            
            replaced_runners = [runner for runner in current_runners if runner not in incomming_runners]
            replacement_runners = [runner for runner in incomming_runners if runner not in current_runners]
            
            # Count the number of max allowed scratched runners to be replaced
            # if len(replaced_runners) > 3:
                # raise serializers.ValidationError({'detail': 'The maximum number of allowed scratched runner replacements has been reached!'})
            
            # if replaced_scratches_count + len(replaced_runners) > 3:
                # raise serializers.ValidationError({'detail': 'The maximum number of allowed scratched runner replacements has been reached!'})
            
            # for runner_id in replaced_runners:
            #     runner_obj = Runner.objects.get(id=runner_id)
            #     if not runner_obj.scratched:
            #         raise serializers.ValidationError({'detail': 'You can not replace a non scratched runner!'})
            
            if race_status == "NOT_STARTED" and datetime.now() < race_date_time:
                runners_data = validated_data.pop('runners', None)
                instance = super().update(instance, validated_data)
                instance.replaced_scratches_count = len(replaced_runners)
                instance.save()
                if runners_data is not None:
                    instance.runners.set(runners_data)
            else:
                for runner_id in replaced_runners:
                    runner_obj = Runner.objects.get(id=runner_id)
                    if not runner_obj.scratched:
                        raise serializers.ValidationError({'detail': 'You can not replace a non scratched runner!'})
                    
                    runner_obj = Runner.objects.get(id=runner_id)
                    racecard_id = runner_obj.racecard.id
                    race_number = runner_obj.race_number
                    
                    races = Racecard.objects.get(id=racecard_id).races
                    for race in races:
                        if race["race_number"] == race_number:
                            race_status = race['status']
                            race_date_time =  datetime.combine(datetime.strptime(race['post_time'], '%I:%M%p'), datetime.strptime(race['adjusted_date'], "%Y-%m-%d").time())
                        
                            if not race_status == "NOT_STARTED" and datetime.now() < race_date_time:
                                raise serializers.ValidationError({'detail': 'Race already started or completed, You can not replace this runner with another runner!'})
                            
                for runner_id in replacement_runners:
                    runner_obj = Runner.objects.get(id=runner_id)
                    if runner_obj.scratched:
                        raise serializers.ValidationError({'detail': 'You can not replace a scratched runner!'})
                    
                    runner_obj = Runner.objects.get(id=runner_id)
                    racecard_id = runner_obj.racecard.id
                    race_number = runner_obj.race_number
                    
                    races = Racecard.objects.get(id=racecard_id).races
                    for race in races:
                        if race["race_number"] == race_number:
                            race_status = race['status']
                            race_date_time =  datetime.combine(datetime.strptime(race['post_time'], '%I:%M%p'), datetime.strptime(race['adjusted_date'], "%Y-%m-%d").time())
                        
                            if not race_status == "NOT_STARTED" and datetime.now < race_date_time:
                                raise serializers.ValidationError({'detail': 'Race already started or completed, You can not use this runner as a replacement!'})     
                
                runners_data = validated_data.pop('runners', None)
                instance = super().update(instance, validated_data)
                instance.replaced_scratches_count = len(replaced_runners)
                instance.save()
                if runners_data is not None:
                    instance.runners.set(runners_data)
        else:
            instance = super().update(instance, validated_data)
            
        return instance
      
class RunnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Runner
        
        fields = (
            'id',
            'external_id',
            'name',
            'racecard',
            'scratched',
            'scratched_datetime',
            'post_position',
            'program_number',
            'trainer',
            'jockey',
            'owner',
            'race_number',
            'odds',
            'salary',
            'coupled',
            'coupled_indicator',
            'created_at',
            'updated_at',
            'margin',
            'score',
            'finish',
            'disqualified',
            'stable_count',
            'total_stables',
        )

        read_only_fields = (
            'salary',
            'margin',
            'points',
            'score',
            'stable_count',
            'total_stables',
        )

class RunnerDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Runner
        fields = (
            'id',
            'external_id',
            'name',
            'racecard',
            'scratched',
            'scratched_datetime',
            'post_position',
            'program_number',
            'trainer',
            'jockey',
            'owner',
            'pedigree',
            'race_number',
            'odds',
            'salary',
            'coupled',
            'coupled_indicator',
            'created_at',
            'updated_at',
            'margin',
            'score',
            'finish',
            'disqualified',
            'career_stats',
            'past_performance',
            'workouts',
            'stable_count',
            'total_stables',
            'custom_stats'
        )

        read_only_fields = (
            'salary',
            'margin',
            'points',
            'score',
            'pedigree',
            'career_stats',
            'past_performance',
            'workouts',
            'stable_count',
            'total_stables',
            'custom_stats'

        )
