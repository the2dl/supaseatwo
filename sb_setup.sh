#!/bin/bash

log() {
    timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    echo "[$timestamp] $1"
}

# Function to generate a random 16-character password (Bash-only)
generate_password() {
    local length=16
    local charset="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-=[]{}|;:,.<>?"
    local password=""
    for i in $(seq 1 $length); do
        random_char_index=$((RANDOM % ${#charset}))
        password+=${charset:$random_char_index:1}
    done
    echo "$password"
}

# Deployment Question
log "Are you starting a new supaseatwo deployment? (yes/no)"
read deployment_answer
log "Your answer: $deployment_answer"

if [ "$deployment_answer" != "yes" ]; then
    log "Exiting script."
    exit 1
fi

# Authentication Question
log "Have you already authenticated with the Supabase CLI? (yes/no)"
read auth_answer
log "Your answer: $auth_answer"

if [ "$auth_answer" != "yes" ]; then
    # Signup and Installation
    log "Please sign up for Supabase: https://supabase.com/dashboard/sign-in"
    
    # OS Selection and Installation
    log "Select your operating system:"
    PS3='Please enter your choice: '
    options=("MacOS" "Windows" "Linux")
    select opt in "${options[@]}"
    do
        case $opt in
            "MacOS")
                brew install supabase/tap/supabase
                ;;
            "Windows")
                log "Download the Supabase CLI from: https://github.com/supabase/cli/releases"
                log "Use scoop or download the supabase_windows binary for your architecture."
                ;;
            "Linux")
                log "Download the Supabase CLI from: https://github.com/supabase/cli/releases"
                log "Download the deb or RPM and install."
                ;;
            *) log "Invalid option";;
        esac
        break
    done

    # Login
    log "Running: supabase login"
    supabase login
fi

# Grab latest supaseatwo
log "Cloning supaseatwo repository..."
git clone https://github.com/the2dl/supaseatwo.git

# Organization Creation
log "Enter your organization name:"
read org_name
log "Running: supabase orgs create $org_name"
org_create_output=$(supabase orgs create "$org_name")
org_id=$(echo "$org_create_output" | awk '{print $NF}')
log "Organization creation output: $org_create_output"
log "Organization ID: $org_id"

# Generate Password (Improved Bash method)
password=$(generate_password)
log "Generated database password: $password"

# Project Creation
log "Enter your project name:"
read project_name
log "Running: supabase projects create $project_name --org-id $org_id --db-password $password --region us-east-1"
project_create_output=$(supabase projects create "$project_name" --org-id "$org_id" --db-password "$password" --region us-east-1)
log "Project creation output: $project_create_output"

# Extract Project URL and ID (from project_create_output)
project_url=$(echo "$project_create_output" | sed -n 's/.*at \(.*\)$/\1/p')
project_id=$(echo "$project_url" | sed -n 's/.*project\/\(.*\)$/\1/p')  # Corrected regex

log "Extracted project ID: $project_id"

echo "Waiting 90 seconds for project initialization..."
sleep 90

# Retrieve API URL, Anon Key, and Service Role Key (using project ref)
log "Running: supabase projects api-keys list --project-ref $project_id"
keys_output=$(supabase projects api-keys list --project-ref "$project_id")

api_url="https://$project_id.supabase.co"

anon_key=""
service_role_key=""

while IFS= read -r line; do
    if [[ $line == *"anon"* ]]; then
        # Extract everything after the first pipe (|) and remove spaces
        key_value=$(echo "$line" | cut -d'│' -f2- | tr -d ' ')
        # Remove "anon│" prefix
        anon_key=$(echo "$key_value" | sed 's/^anon│//')
    elif [[ $line == *"service_role"* ]]; then
        # Extract everything after the first pipe (|) and remove spaces
        key_value=$(echo "$line" | cut -d'│' -f2- | tr -d ' ')
        # Remove "service_role│" prefix
        service_role_key=$(echo "$key_value" | sed 's/^service_role│//')
    fi
done <<< "$keys_output"

log "Extracted API URL: $api_url"
log "Extracted anon key: $anon_key"
log "Extracted service_role key: $service_role_key"
log "Constructed dashboard URL: $project_url"

# Database Setup (Corrected to use project id and include password)
export PGPASSWORD="$password"
log "Running: psql -h aws-0-us-east-1.pooler.supabase.com -p 6543 -d postgres -U postgres.$project_id"
psql_output=$(psql -h aws-0-us-east-1.pooler.supabase.com -p 6543 -d postgres -U "postgres.$project_id" -f "$(pwd)/supaseatwo/supa.sql")
log "psql output: $psql_output"

if echo "$psql_output" | grep -q "FATAL"; then
    log "Database setup failed."
else
    log "Database setup successful."
fi

# Summary for the User
log "Summary:"
log "1) Org Name: $org_name, Org ID: $org_id"
log "2) Project Name: $project_name"
log "3) Project URL: $project_url"
log "4) API URL: $api_url"
log "5) Database Password: $password"
log "6) Anon Key: $anon_key"
log "7) Service Role Key: $service_role_key"
log "8) Status: Database Setup $(if echo "$psql_output" | grep -q "FATAL"; then echo "Failure"; else echo "Success"; fi)"

