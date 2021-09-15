#RAM 512MO, WSET 10000 pages
iter=5

for i in `seq 1 $iter`
do
    ../../bench.py -v --vm-memory 512
    ../../bench.py -f --vm-memory 512
done

for i in `seq 1 $iter`
do
    ../../bench.py -v --vm-memory 1024
    ../../bench.py -f --vm-memory 1024
done

for i in `seq 1 $iter`
do
    ../../bench.py -v --vm-memory 2048
    ../../bench.py -f --vm-memory 2048
done


for i in `seq 1 $iter`
do
    ../../bench.py -v --vm-memory 4096
    ../../bench.py -f --vm-memory 4096
done


for i in `seq 1 $iter`
do
    ../../bench.py -v --vm-memory 8192
    ../../bench.py -f --vm-memory 8192
done
