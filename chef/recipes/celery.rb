#
# Cookbook Name:: chef-stableduel
# Recipe:: celery
#
# Copyright (C) Stable Duel
#
# All rights reserved - Do Not Redistribute
#

if Dir.exists? "/home/vagrant"
  user = "vagrant"
else
  user = "ubuntu"
end

app = user == "vagrant" ? node['stableduel'] : search('aws_opsworks_app').first

config = app['environment']


# Create celery user and working directory
group 'celery' do
  system true
end
user 'celery' do
  group 'celery'
  system true
  manage_home false
end

# Add user to www-data group
execute "add_user_to_group" do
  command "usermod -a -G www-data celery"
end

# Create log file for daemon
directory "/var/log/celery" do
  recursive true
  user 'celery'
  group 'celery'
end

# Celery config
directory "/etc/celery" do
  recursive true
end
template '/etc/celery/celery.conf' do
  source 'celery.conf'
  variables(
    :user => "#{user}",
  )
end

# Declare redis service
template '/etc/systemd/system/celery.service' do
  source 'celery.service'
  variables(
    :user => "#{user}",
  )
end
bash "reload_service_config" do
  code "systemctl daemon-reload"
end

# Enable and restart the service
service 'celery' do
  action [ :enable, :restart ]
end
