#!/bin/bash
work=$(dirname $(readlink -f "$0"))

role_name=$1

if [ $# -lt 1 ]; then
  echo "usage: $0  <role_name>"
  exit 1
fi


#work_path=$work/$role_name
roles_path=$work/playbooks/roles/$role_name

#mkdir -p $work_path
#mkdir -p $work_path/group_vars
mkdir -p $roles_path/defaults
mkdir -p $roles_path/tasks
mkdir -p $roles_path/handlers
mkdir -p $roles_path/templates
mkdir -p $roles_path/files
mkdir -p $roles_path/vars
mkdir -p $roles_path/meta

touch $roles_path/defaults/main.yml
touch $roles_path/tasks/main.yml
touch $roles_path/handlers/main.yml
touch $roles_path/vars/main.yml
touch $roles_path/meta/main.yml
