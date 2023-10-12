#
# Cookbook Name:: chef-stableduel
# Recipe:: system
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

virtualenv = "/home/#{user}/env"

# Add repository for python3.7
apt_repository 'deadsnakes' do
  uri 'ppa:deadsnakes'
end

apt_update 'update'

package 'system_packages' do
  package_name [
    'git',
    'libpq-dev',
    'build-essential'
  ]
  action :install
end

python_runtime '3.7' do
  options package_name: 'python3.7'
end

python_package 'virtualenv' do
  action :install
end

# NOTE: This will fail with SSL errors if owner/group isn't specified
python_virtualenv "#{virtualenv}" do
  python '/usr/bin/python3.7'
  user user
  group user
  action :create
end
