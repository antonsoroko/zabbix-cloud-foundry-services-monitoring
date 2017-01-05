#!/bin/bash

stat=$1

. /etc/zabbix/scripts/.rab.auth

FIRST_ELEMENT=1
function json_head {
    printf "{";
    printf "\"data\":[";    
}

function json_end {
    printf "]";
    printf "}";
}

function check_first_element {
    if [[ $FIRST_ELEMENT -ne 1 ]]; then
        printf ","
    fi
    FIRST_ELEMENT=0
}

function discovery()
{
    queues=$(curl -s -u $USER:$PASS http://172.29.0.85:15672/api/queues | jq '.[] | .name')
    json_head
    for queue in $queues
    do
        check_first_element
        printf "{"
        printf "\"{#QUEUENAME}\":$queue"
        printf "}"
    done
    json_end
}

function deliver()
{
    deliver_details=`curl -s -u $USER:$PASS http://172.29.0.85:15672/api/overview | jq .message_stats.deliver_get_details.rate`
    echo $deliver_details
}

function publish()
{
    publish_details=`curl -s -u $USER:$PASS http://172.29.0.85:15672/api/overview | jq .message_stats.publish_details.rate`
    echo $publish_details
}

function get_queue_stats()
{
    queue_id=$1
    metric=$2
    details=`curl -s -u $USER:$PASS http://172.29.0.85:15672/api/queues | jq --arg id "$queue_id" '.[] | select(.name==$id)' | jq .$metric`
    echo $details
}

case "$stat" in
        discovery)
            discovery
            ;;
        deliver)
            deliver
            ;;
        publish)
            publish
            ;;
        queue)
            queue_id=$2
            metric=$3
            get_queue_stats $queue_id $metric
            ;;
        *)
            echo $"Usage: $0 {discovery|deliver|publish|queue <queue_id>}"
            exit 1
esac
