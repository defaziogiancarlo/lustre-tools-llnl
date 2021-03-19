#!/bin/bash
# test the python functions

conda init bash

LC2="conda activate llnl2 && python /home/defazio1/lustre-tools-llnl/scripts/llogcolor2.py"
LC3="conda activate llnl3 && python /home/defazio1/lustre-tools-llnl/scripts/llogcolor3.py"


SAMPLE=/home/defazio1/lustre-tools-llnl/scripts/color_samples
TMP=/tmp/llogtest


mkdir $TMP


$LC2 -P $SAMPLE/sample_logs > $TMP/2_sample_logs
$LC3 -P $SAMPLE/sample_logs > $TMP/3_sample_logs

if ! diff $TMP/2_sample_logs $TMP/3_sample_logs;
then
    echo "fail"
fi

rm -r $TMP
