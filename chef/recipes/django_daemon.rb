#
# Cookbook Name:: chef-stableduel
# Recipe:: django_daemon
#
# Copyright (C) Stable Duel
#
# All rights reserved - Do Not Redistribute
#

app = node.attribute?('vagrant') ? node['stableduel'] : search('aws_opsworks_app').first
config = app['environment']
if Dir.exists? "/home/vagrant"
  user = "vagrant"
else
  user = "ubuntu"
end
virtualenv = "/home/#{user}/env"

# Collect static files
bash "collectstatic" do
  user "#{user}"
  code "#{virtualenv}/bin/python manage.py collectstatic --noinput"
  cwd "/home/#{user}/stableduel/djangoapp"
end

# Create log file for daemon
directory "/var/log/stableduel" do
  recursive true
end
file "/var/log/stableduel/djangoapp.log" do
  mode 0666
  action :create_if_missing
end

# Declare djangoapp service
template '/etc/systemd/system/djangoapp.service' do
  source 'djangoapp.service'
  variables(
    :user => "#{user}",
  )
end
bash "reload_service_config" do
  code "systemctl daemon-reload"
end

# Enable and restart the service
service 'djangoapp' do
  action [ :enable, :restart ]
end
