#!/usr/local/bin/bash

## DESCRIPTION: gist utility

## AUTHOR: Hui Zheng

declare -r SCRIPT_NAME=$(basename "$BASH_SOURCE" .sh)

## exit the shell(default status code: 1) after printing the message to stderr
bail() {
    echo -ne "$1" >&2
    exit ${2-1}
} 

## help message
declare -r HELP_MSG="Usage: $SCRIPT_NAME [OPTION]...[]
  -h       display this help and exit
  -l       list gists
  -i       check in(pull) gists
  -o       check out(push) gists
  -C       change to directory
"

## print the usage and exit the shell(default status code: 2)
usage() {
    declare status=2
    if [[ "$1" =~ ^[0-9]+$ ]]; then
        status=$1
        shift
    fi
    bail "${1}$HELP_MSG" $status
}

declare dry_run=false
declare work_dir=.

while getopts ":hlinoC:" opt; do
    case $opt in
        h)
            usage 0
            ;;
        l)
            command="list"
            ;;
        i)
            command="pull"
            ;;
        o)
            command="push"
            ;;
        n)
            dry_run=true
            ;;
        C)
            work_dir="$OPTARG"
            ;;
        \?)
            usage "Invalid option: -$OPTARG \n"
            ;;
    esac
done

shift $(($OPTIND - 1))
[[ "$#" -lt 0 ]] && usage "Too few arguments\n"

#==========MAIN CODE BELOW==========

list() {
    gist -l
}

pull() {
    while IFS=$'\n' read -r gist; do
        do_pull $gist
    done <<< "$(gist -l)"
}

do_pull() {
    gist_url=${1#https://}
    gist_id=${gist_url##*/}
    gist_url=git@${gist_url%/*}:$gist_id
    shift
    caption=$*
    # [title] description #tag1 #tag2 (secret)
    if [[ "$caption" =~ ^[\ [](.*)[]\ ]\ +([^#]*)(\ #.+)*[^#]*\(secret\)$ ]]; then
        title=${BASH_REMATCH[1]} 
        desc=${BASH_REMATCH[2]} 
        tags=${BASH_REMATCH[3]} 
        # echo caption: [$caption], title: [$title], desc: [$desc], tags: [$tags]
        IFS=' #' read -r -a array <<< "$tags"
        for tag in "${array[@]}"
        do
            : #echo "[$tag]"
        done
        if [ -d "$gist_id" ]; then
            echo "pulling " $gist_url
            cd "$gist_id"
            exec git pull
            cd ..
        else
            echo "cloning " $gist_url
            exec git clone $gist_url
        fi
    fi
}

push() {
    for dir in *; do
        (cd "$dir" && do_push)
    done
}

do_push() {
    exec "git add -A && git commit -m 'commit via congist' && git push"
}

exec() {
    if [ "$dry_run" = true ]; then
        echo dry run: $*
    else
        eval "$*"
    fi
}

eval "cd $work_dir && $command"
