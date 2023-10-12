#
# Cookbook Name:: chef-stableduel
# Recipe:: dev_database
#
# Copyright (C) Stable Duel
#
# All rights reserved - Do Not Redistribute

package "postgresql"
package "postgresql-contrib"


bash 'set postgres password' do
  code "sudo -u postgres psql -U postgres -d template1 -c \"ALTER USER postgres WITH PASSWORD 'password';\""
end

bash 'createdb' do
  code "PGPASSWORD=password psql -h 127.0.0.1 -U postgres -c 'CREATE DATABASE stableduel'"
  ignore_failure true
end
