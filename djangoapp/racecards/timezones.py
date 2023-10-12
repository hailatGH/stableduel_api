import re
import pytz

TZ_STRING = """
ABT,ALBERTA DOWNS,M,Lacombe,AB,CAN,Canada/Mountain
AJX,AJAX DOWNS,E,Ajax,ON,CAN,Canada/Eastern
ASD,ASSINIBOIA DOWNS,C,Winnipeg,MB,CAN,Canada/Central
CTD,CENTURY DOWNS,M,Rocky View County,AB,CAN,Canada/Mountain
CTM,CENTURY MILE,M,Edmonton,AB,CAN,Canada/Mountain
DEP,DESERT PARK,P,Osoyoos,BC,CAN,Canada/Pacific
FE,FORT ERIE,E,Fort Erie,ON,CAN,Canada/Eastern
GPR,GRANDE PRAIRIE,M,Grande Prairie,AB,CAN,Canada/Mountain
HST,HASTINGS RACECOURSE,P,Vancouver,BC,CAN,Canada/Pacific
LBG,LETHBRIDGE,M,Lethbridge,AB,CAN,Canada/Mountain
MD,MARQUIS DOWNS,M,Saskatoon,SK,CAN,Canada/Central
MIL,MILLARVILLE,M,Millarville,AB,CAN,Canada/Mountain
NP,NORTHLANDS PARK,M,Edmonton,AB,CAN,Canada/Mountain
WO,WOODBINE,E,Rexdale,ON,CAN,Canada/Eastern
CMR,CAMARERO RACE TRACK,E,,Canovanas,PR,America/Puerto_Rico
AIK,AIKEN,E,Aiken,SC,USA,US/Eastern
ALB,ALBUQUERQUE,M,Albuquerque,NM,USA,US/Mountain
AP,ARLINGTON,C,Arlington Heights,IL,USA,US/Central
AQU,AQUEDUCT,E,Ozone Park,NY,USA,US/Eastern
ARP,ARAPAHOE PARK,M,Aurora,CO,USA,US/Mountain
ATH,ATLANTA,E,Kingston,GA,USA,US/Eastern
ATO,ATOKAD DOWNS,C,South Sioux City,NE,USA,US/Mountain
BCF,BROWN COUNTY FAIR,C,Brown County,SD,USA,US/Central
BEL,BELMONT PARK,E,Elmont,NY,USA,US/Eastern
BKF,BLACK FOOT,M,Blackfoot,ID,USA,US/Mountain
BRN,HARNEY COUNTY FAIR,P,Burns,OR,USA,US/Pacific
BTP,BELTERRA PARK,E,Cincinnati,OH,USA,US/Eastern
CAM,CAMDEN,E,Camden,SC,USA,US/Eastern
CAS,CASSIA COUNTY FAIR,M,Burley,ID,USA,US/Mountain
CBY,CANTERBURY PARK,C,Shakopee,MN,USA,US/Central
CD, CHURCHILL DOWNS,E,Louisville,KY,USA,US/Eastern
CHA,CHARLESTON,E,Charleston,SC,USA,US/Eastern
CHL,CHARLOTTE,E,Charlotte,NC,USA,US/Eastern
CLS,COLUMBUS,C,Columbus,NE,USA,US/Mountain
CNL,COLONIAL DOWNS,E,New Kent,VA,USA,US/Eastern
CPW,CHIPPEWA DOWNS,C,Belcourt,ND,USA,US/Central
CT,HOLLYWOOD CASINO AT CHARLES TOWN RACES,E,Charles Town,WV,USA,US/Eastern
CT1,HOLLYWOOD CASINO AT CHARLES TOWN RACES LAST 5,E,Charles Town,WV,USA,US/Eastern
CWF,CENTRAL WYOMING FAIR,M,Casper,WY,USA,US/Mountain
DED,DELTA DOWNS,C,Vinton,LA,USA,US/Central
DEL,DELAWARE PARK,E,Wilmington,DE,USA,US/Eastern
DG,COCHISE COUNTY FAIR @ DOUGLAS,M,Douglas,AZ,USA,US/Arizona
DMR,DEL MAR,P,Del Mar,CA,USA,US/Pacific
DXD,DIXIE DOWNS,M,St. George,UT,USA,US/Mountain
ED,ENERGY DOWNS,M,Gillette,WY,USA,US/Mountain
ELK,ELKO COUNTY FAIR,P,Elko,NV,USA,US/Pacific
ELP,ELLIS PARK,C,Henderson,KY,USA,US/Central
ELY,WHITE PINE RACING,P,Ely,NV,USA,US/Pacific
EMD,EMERALD DOWNS,P,Auburn,WA,USA,US/Pacific
EVD,EVANGELINE DOWNS,C,Opelousas,LA,USA,US/Central
FAI,FAIR HILL,E,Fair Hill,MD,USA,US/Eastern
FAR,NORTH DAKOTA HORSE PARK,C,Fargo,ND,USA,US/Central
FER,FERNDALE,P,Ferndale,CA,USA,US/Pacific
FG,FAIR GROUNDS,C,New Orleans,LA,USA,US/Central
FH,FAR HILLS,E,Far Hills,NJ,USA,US/Eastern
FL,FINGER LAKES,E,Farmington,NY,USA,US/Eastern
FMT,FAIR MEADOWS,C,Tulsa,OK,USA,US/Central
FNO,FRESNO,P,Fresno,CA,USA,US/Pacific
FON,FONNER PARK,C,  Grand Island,NE,USA,US/Mountain
FP,FAIRMOUNT PARK,C,Collinsville,IL,USA,US/Central
FPL,FAIR PLAY PARK,C,Hastings,NE,USA,US/Mountain
FPX,FAIRPLEX PARK,P,Pomona,CA,USA,US/Pacific
FTP,FORT PIERRE,C,Pierre,SD,USA,US/Central
FX,FOXFIELD,E,Charlottesville,VA,USA,US/Eastern
GF,GREAT FALLS,M,Great Falls,MT,USA,US/Mountain
GG,GOLDEN GATE FIELDS,P,Albany,CA,USA,US/Pacific
GIL,GILLESPIE COUNTY FAIRGROUND,C,Fredericksburg,TX, USA,US/Central
GLN,GLYNDON,E,Glyndon,MD,USA,US/Eastern
GN,GRAND NATIONAL,E,Butler,MD,USA,US/Eastern
GP,GULFSTREAM PARK,E,Hallandale,FL,USA,US/Eastern
GPW,GULFSTREAM PARK WEST,E,Miami,FL,USA,US/Eastern
GRM,GREAT MEADOW,E,The Plains,VA,USA,US/Eastern
GRP,GRANTS PASS,P,Grants Pass,OR,USA,US/Pacific
GV,GENESEE VALLEY,E,Geneseo,NY,USA,US/Eastern
HAW,HAWTHORNE,C,Stickney,IL,USA,US/Central
HIA,HIALEAH PARK,E,Hialeah,FL,USA,US/Eastern
HOU,SAM HOUSTON RACE PARK,C,Houston,TX,USA,US/Central
HP,HAZEL PARK,E,Hazel Park,MI,USA,US/Michigan
HPO,HORSEMEN'S PARK,C,Omaha,NE,USA,US/Mountain
IND,INDIANA GRAND RACE COURSE,E,Shelbyville,IN,USA,US/Eastern
JRM,JEROME COUNTY FAIR,M,Jerome,ID,USA,US/Mountain
KD,KENTUCKY DOWNS,C,Franklin,KY,USA,US/Eastern
KEE,KEENELAND,E,Lexington,KY,USA,US/Eastern
LA,LOS ALAMITOS,P,Los Alamitos,CA,USA,US/Pacific
LAD,LOUISIANA DOWNS,C,Bossier City,LA,USA,US/Central
LBT,LAUREL BROWN RACETRACK,M,South Jordan,UT,USA,US/Mountain
LEX,LEXINGTON,E,Lexington,KY,USA,US/Eastern
LNN,LINCOLN RACE COURSE,C,Lincoln,NE,USA,US/Mountain
LRC,LOS ALAMITOS RACE COURSE,P,Los Alamitos,CA,USA,US/Pacific
LRL,LAUREL PARK,E,Laurel,MD,USA,US/Eastern
LS,LONE STAR PARK,C,Grand Prairie,TX,USA,US/Central
MAL,MALVERN,E,Malvern,PA,USA,US/Eastern
MC,MILES CITY,M,Miles City,MT,USA,US/Mountain
MED,MEADOWLANDS,E,East Rutherford,NJ,USA,US/Eastern
MID,GLENWOOD PARK AT MIDDLEBURG,E,Middleburg,VA,USA,US/Eastern
MNR,MOUNTAINEER CASINO RACETRACK & RESORT,E,Chester,WV,USA,US/Eastern
MON,MONKTON,E,Monkton,MD,USA,US/Eastern
MS,MILL SPRING,E,Mill Spring,NC,USA,US/Eastern
MTH,MONMOUTH PARK,E,Oceanport,NJ,USA,US/Eastern
MTP,MONTPELIER,E,Montpelier Station,VA,USA,US/Eastern
MVR,MAHONING VALLEY RACE COURSE,E,Youngstown,OH,USA,US/Eastern
ONE,ONEIDA COUNTY FAIR,M,Malad,ID,USA,US/Mountain
OP,OAKLAWN PARK,C,Hot Springs,AR,USA,US/Central
OTC,OCALA TRAINING CENTER,E,Ocala,FL,USA,US/Eastern
OTP,OAK TREE AT PLEASANTON,P,Pleasanton,CA,USA,US/Pacific
PEN,PENN NATIONAL,E,Grantville,PA,USA,US/Eastern
PID,PRESQUE ISLE DOWNS,E,Erie,PA,USA,US/Eastern
PIM,PIMLICO,E,Baltimore,MD,USA,US/Eastern
PM,PORTLAND MEADOWS,P,Portland,OR,USA,US/Pacific
PMT,PINE MTN-CALLAWAY GARDEN,E,Pine Mountain,GA,USA,US/Eastern
POD,POCATELLO DOWNS,M,Pocatello,ID,USA,US/Mountain
PRM,PRAIRIE MEADOWS,C,Altoona,IA,USA,US/Central
PRV,CROOKED RIVER ROUNDUP,P,Prineville,OR,USA,US/Pacific
PRX,PARX RACING,E,Bensalem,PA,USA,US/Eastern
PW,PERCY WARNER,C,Nashville,TN,USA,US/Central
RET,RETAMA PARK,C,San Antonio,TX,USA,US/Central
RIL,RILLITO,M,Tucson,AZ,USA,US/Arizona
RP,REMINGTON PARK,C,Oklahoma City,OK,USA,US/Central
RUI,RUIDOSO DOWNS,M,Ruidoso Downs,NM,USA,US/Mountain
RUP,RUPERT DOWNS,M,Rupert,ID,USA,US/Mountain
SA,SANTA ANITA PARK,P,Arcadia,CA,USA,US/Pacific
SAC,SACRAMENTO,P,Sacramento,CA,USA,US/Pacific
SAF,GRAHAM COUNTY FAIR @ SAFFORD,M,Safford,AZ,USA,US/Arizona
SAR,SARATOGA,E,Saratoga Springs,NY,USA,US/Eastern
SDY,SANDY DOWNS,M,Idaho Falls,ID,USA,US/Mountain
SHW,SHAWAN DOWNS,E,Butler,MD,USA,US/Eastern
SON,SANTA CRUZ COUNTY FAIR @ SONOITA,M,Sonoita,AZ,USA,US/Arizona
SR, SANTA ROSA,P,Santa Rosa,CA,USA,US/Pacific
SRP,SUNRAY PARK,M,Farmington,NM,USA,US/Mountain
STN,STONEYBROOK AT FIVE POINTS,E,Raeford,NC,USA,US/Eastern
SUD,SUN DOWNS,P,Kennewick,WA,USA,US/Pacific
SUF,SUFFOLK DOWNS,E,East Boston,MA,USA,US/Eastern
SUN,SUNLAND PARK,M,Sunland Park,NM,USA,US/Mountain
SWF,SWEETWATER DOWNS,M,Rock Springs,WY,USA,US/Mountain
TAM,TAMPA BAY DOWNS,E,Oldsmar,FL,USA,US/Eastern
TDN,THISTLEDOWN,E,North Randall,OH,USA,US/Eastern
TIL,TILLAMOOK COUNTY FAIR,P,Tillamook,OR,USA,US/Pacific
TIM,TIMONIUM,E,Timonium,MD,USA,US/Eastern
TP,TURFWAY PARK,E,Florence,KY,USA,US/Eastern
TRY,TRYON,E,Tryon,NC,USA,US/Eastern
TUP,TURF PARADISE,M,Phoenix,AZ,USA,America/Phoenix
UN,EASTERN OREGON LIVESTOCK SHOW,P,Union,OR,USA,US/Pacific
UNI,PENNSYLVANIA HUNT CUP,E,Unionville,PA,USA,US/Eastern
WBR,WEBER DOWNS,M,Ogden,UT,USA,US/Mountain
WIL,WILLOWDALE STEEPLECHASE,E,Kennett Square,PA,USA,US/Eastern
WNT,WINTERTHUR,E,Winterthur,DE,USA,US/Eastern
WRD,WILL ROGERS DOWNS,C,Claremore,OK,USA,US/Central
WYO,WYOMING DOWNS,M,Evanston,WY,USA,US/Mountain
ZIA,ZIA PARK,M,Hobbs,NM,USA,US/Mountain
DUB,MEYDAN,E,DUBAI,DUBAI,UAE,US/Eastern
WOL,WOLVERHAMPTON,E,WOLVERHAMPTON,ENG,UK,US/Eastern
CHM,CHELTENHAM,E,CHELTENHAM,ENG,UK,US/Eastern
KEL,KELSO,E,KELSO,ENG,UK,US/Eastern
TAU,TAUNTON,E,TAUNTON,ENG,UK,US/Eastern
HAY,HAYDOCK,E,HAYDOCK,ENG,UK,US/Eastern
SED,SEDGEFIELD,E,SEDGEFIELD,ENG,UK,US/Eastern
XGA,X GAMES,M,ASPEN,CO,USA,US/Mountain
RAS,ROYAL ASCOT,E,ASCOT,ENG,UK,US/Eastern


YRX,YONKERS RACEWAY,E,GOSHEN,NY,USA,US/Eastern
STG,SARATOGA HARNESS,E,PLAINVILLE,CT,USA,US/Eastern
SCD,SCIOTO DOWNS,P,SACRAMENTO,CA,USA,US/Mountain
PRM,PRAIRIE MEADOWS,M,PHOENIX,AZ,USA,US/Mountain
PHL,HARRAH'S PHILADELPHIA,E,PHILADELPHIA,PA,USA,US/Eastern
PCD,POCONO DOWNS,E,MIDDLETOWN,DE,USA,US/Eastern
NOR,NORTHVILLE DOWNS,E,TORONTO,ON,CANADA,US/Eastern
MOH,MOHAWK RACETRACK,E,KINGSTON,ON,CANADA,US/Eastern
MEA,THE MEADOWS,E,SYLVANIA,OH,USA,US/Eastern
MXX,MEADOWLANDS,M,BALZAC,AB,CANADA,US/Mountain
LEX,THE RED MILE,E,LEXINGTON,KY,USA,US/Eastern
HOP,HOOSIER PARK,E,SAUGERTIES,NY,USA,US/Eastern
DEL,DELAWARE COUNTY FAIR,E,DELAWARE,OH,USA,US/Eastern
CNM,CENTURY MILE,M,ALBUQUERQUE,NM,USA,US/Mountain
CHS,HARRAH'S CHESTER,E,HANOVER,PA,USA,US/Eastern
CAL,CAL-EXPO,P,MISSION,BC,CANADA,US/Pacific
BAN,BANGOR-HOLLYWOOD SLOTS,E,BANGOR,ME,USA,US/Eastern
"""



UTC_OFFSETS = {'E': "-0500",
               "C": "-0600",
               "M": "-0700",
               "P": "-0800",
               "D": "+0400",
               "G": "+0000",
               "A": "-0400",
               "N": "-0300",}


class TimeZone():
    def __init__(self, track_name, track_code, abbrev, time_zone):

        self.track_name = track_name
        self.track_code = track_code
        self.abbrev = abbrev
        #Include DST here if warranted
        self.utc_offset = UTC_OFFSETS[abbrev]
        self.tz = pytz.timezone(time_zone)
        self.time_delta = (int(self.utc_offset) / 100) * -1

TIMEZONE_BY_TRACK_CODE = {}

for track_line in TZ_STRING.split("\n"):

    if len(track_line) > 0:
        #print(track_line)
        #print(track_line.split(" "))
        (track_code, track_name, timezone_abbrev, city, state, country, time_zone) = track_line.split(",")
        tz = TimeZone(track_line, track_code, timezone_abbrev,time_zone)
        TIMEZONE_BY_TRACK_CODE[track_code] = tz
    


def get_timezone(track_code):
    return TIMEZONE_BY_TRACK_CODE.get(track_code)




def calculate_timezone_harness(track_name, track_code, timezone_abbrev,time_zone):
    track_name = track_name
    track_code = track_code
    timezone_abbrev = timezone_abbrev
    time_zone = time_zone
    tzh = TimeZone(track_name, track_code, timezone_abbrev,time_zone)

    return tzh

