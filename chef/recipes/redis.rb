#
# Cookbook Name:: chef-stableduel
# Recipe:: redis
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


# Install redis if not already
remote_file '/tmp/redis-stable.tar.gz' do
  source 'http://download.redis.io/redis-stable.tar.gz'
  owner "#{user}"
  group "#{user}"
  mode '0755'
  action :create
  not_if "sh -c 'command -v redis-server'"
  notifies :run, 'execute[extract_redis]', :immediately
end

execute 'extract_redis' do
  command 'tar xzvf redis-stable.tar.gz'
  cwd '/tmp'
  notifies :run, 'execute[build_redis]', :immediately
  action :nothing
end

execute 'build_redis' do
  command 'make'
  cwd '/tmp/redis-stable'
  notifies :run, 'execute[install_redis]', :immediately
  action :nothing
end

execute 'install_redis' do
  command 'make install'
  cwd '/tmp/redis-stable'
  notifies :run, 'execute[cleanup_redis]', :immediately
  action :nothing
end

execute 'cleanup_redis' do
  command command <<-EOF
    rm redis-stable.tar.gz
    rm -rf redis-stable
  EOF
  cwd '/tmp'
  action :nothing
end

# Create log file for daemon
directory "/var/log/stableduel" do
  recursive true
end
file "/var/log/stableduel/redis.log" do
  mode 0666
  action :create_if_missing
end

# Redis config
directory "/etc/redis" do
  recursive true
end
cookbook_file "/etc/redis/redis.conf" do
  source 'redis.conf'
end

# Create redis user and working directory
group 'redis' do
  system true
end
user 'redis' do
  group 'redis'
  system true
  manage_home false
end
directory "/var/lib/redis" do
  recursive true
  user 'redis'
  group 'redis'
  mode '0770'
  action :create
end

# Declare redis service
cookbook_file "/etc/systemd/system/redis.service" do
  source 'redis.service'
end
bash "reload_service_config" do
  code "systemctl daemon-reload"
end

# Enable and restart the service
service 'redis' do
  action [ :enable, :restart ]
end
