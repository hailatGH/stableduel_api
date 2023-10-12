#
# Cookbook Name:: chef-stableduel
# Recipe:: code
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

app = search('aws_opsworks_app').first
git_ssh_key = "#{app['app_source']['ssh_key']}"
git_url = "#{app['app_source']['url']}"
git_revision = "#{app['app_source']['revision']}" ? "#{app['app_source']['revision']}" : "master"



# Put the file on the node
file "/home/#{user}/.ssh/id_rsa" do
  owner "#{user}"
  mode 0400
  content "#{git_ssh_key}"
end

# Configure ssh to use ssh key
cookbook_file "/home/#{user}/.ssh/config" do
  source 'config'
end

#fetch code
git "/home/#{user}/stableduel" do
  repository "#{git_url}"
  reference "#{git_revision}" # branch
  action :sync
  user "#{user}"
  group "#{user}"
end