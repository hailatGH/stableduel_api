#
# Cookbook Name:: chef-stableduel
# Recipe:: server
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

# Install nginx
include_recipe "nginx"

# Setup simple nginx proxy to node port
template '/etc/nginx/sites-available/stableduel' do
  source 'nginx.conf.erb'
  variables(
    :user => user,
  )
  user user
end
nginx_site "stableduel"

service "nginx" do
  action [ :restart ]
end
