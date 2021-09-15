#RAM 512MO, WSET 10000 pages
iter=10

for i in `seq 1 $iter`
do
    ./bench.py -v --vm-memory 2048 --stress-rate 0 --stress-pages 100000 -t 60
    ./bench.py -f --vm-memory 2048 --stress-rate 0 --stress-pages 100000 -t 60
done

for i in `seq 1 $iter`
do
    ./bench.py -v --vm-memory 2048 --stress-rate 10 --stress-pages 100000 -t 60
    ./bench.py -f --vm-memory 2048 --stress-rate 10 --stress-pages 100000 -t 60
done

for i in `seq 1 $iter`
do
    ./bench.py -v --vm-memory 2048 --stress-rate 20 --stress-pages 100000 -t 60
    ./bench.py -f --vm-memory 2048 --stress-rate 20 --stress-pages 100000 -t 60
done


for i in `seq 1 $iter`
do
    ./bench.py -v --vm-memory 2048 --stress-rate 30 --stress-pages 100000 -t 60
    ./bench.py -f --vm-memory 2048 --stress-rate 30 --stress-pages 100000 -t 60
done


for i in `seq 1 $iter`
do
    ./bench.py -v --vm-memory 2048 --stress-rate 40 --stress-pages 100000 -t 60
    ./bench.py -f --vm-memory 2048 --stress-rate 40 --stress-pages 100000 -t 60
done

for i in `seq 1 $iter`
do
    ./bench.py -v --vm-memory 2048 --stress-rate 50 --stress-pages 100000 -t 60
    ./bench.py -f --vm-memory 2048 --stress-rate 50 --stress-pages 100000 -t 60
done

for i in `seq 1 $iter`
do
    ./bench.py -v --vm-memory 2048 --stress-rate 60 --stress-pages 100000 -t 60
    ./bench.py -f --vm-memory 2048 --stress-rate 60 --stress-pages 100000 -t 60
done


for i in `seq 1 $iter`
do
    ./bench.py -v --vm-memory 2048 --stress-rate 70 --stress-pages 100000 -t 60
    ./bench.py -f --vm-memory 2048 --stress-rate 70 --stress-pages 100000 -t 60
done


for i in `seq 1 $iter`
do
    ./bench.py -v --vm-memory 2048 --stress-rate 80 --stress-pages 100000 -t 60
    ./bench.py -f --vm-memory 2048 --stress-rate 80 --stress-pages 100000 -t 60
done



for i in `seq 1 $iter`
do
    ./bench.py -v --vm-memory 2048 --stress-rate 90 --stress-pages 100000 -t 60
    ./bench.py -f --vm-memory 2048 --stress-rate 90 --stress-pages 100000 -t 60
done


for i in `seq 1 $iter`
do
    ./bench.py -v --vm-memory 2048 --stress-rate 100 --stress-pages 100000 -t 60
    ./bench.py -f --vm-memory 2048 --stress-rate 100 --stress-pages 100000 -t 60
done



