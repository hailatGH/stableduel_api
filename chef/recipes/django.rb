#
# Cookbook Name:: chef-stableduel
# Recipe:: django
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


dev = config['dev']
virtualenv = "/home/#{user}/env"
env = config.merge({
  'DJANGO_MEDIA_ROOT' => "/home/#{user}/media",
  'HOME' => "/home/#{user}/"
})

# Add user to www-data group
execute "add_user_to_group" do
  command "usermod -a -G www-data #{user}"
end

# Create media directory
directory 'setup-media-dir' do
  path "/home/#{user}/media"
  owner "www-data"
  group "www-data"
  mode '2775' # setgid gives new files www-data group
  recursive true
  action :create
end
# Copied files will inherit group permissions
execute "set_cache_acl" do
  command "sudo setfacl -Rdm g:www-data:rwx /home/#{user}/media"
end

# Install python dependencies
pip_requirements "/home/#{user}/stableduel/djangoapp/requirements/#{if dev then 'local' else 'production' end}.txt" do
  python "#{virtualenv}/bin/python"
  user user
  group user
end

# Initialize gitignored config using environment
dotenv_path = "/home/#{user}/stableduel/djangoapp/.env"
template "#{dotenv_path}" do
  source 'env.erb'
  owner user
  group user
  mode '0644'
  variables :environment => env
  not_if { dev && ::File.exist?(dotenv_path) }
end

# Apply any migrations
bash "migrate" do
  environment env 
  user "#{user}"
  code "#{virtualenv}/bin/python manage.py migrate --noinput"
  cwd "/home/#{user}/stableduel/djangoapp"
end
