

import pandas as pd
import re
import numpy as np
import matplotlib.pyplot as plt

f_modified = open("./modified.out")
f_vanilla = open("./vanilla.out")

Lines = f_vanilla.readlines()
list_vanilla = []
count = 0
i = 0
for line in Lines:
    count += 1
    pattern = '\d+'
    result = re.findall(pattern, line)
    if i%3 == 0:
        list_vanilla.append([result[1]])
    else:
        list_vanilla[int(i/3)].append(result[0])

    i = i+1

Lines = f_modified.readlines()
list_modified = []
count = 0
i = 0
for line in Lines:
    count += 1
    pattern = '\d+'
    result = re.findall(pattern, line)
    if i%3 == 0:
        list_modified.append([result[1]])
    else:
        list_modified[int(i/3)].append(result[0])

    i = i+1

df_vanilla = pd.DataFrame.from_records(list_vanilla)
df_modified = pd.DataFrame.from_records(list_modified)

df_vanilla.columns = ['dirt_rate', 'total_time', 'down_time']
df_modified.columns = ['dirt_rate', 'total_time', 'down_time']

print(df_modified)

modified_0 = df_modified[df_modified.dirt_rate == "0"].astype(int)
modified_1 = df_modified[df_modified.dirt_rate == "10"].astype(int)
modified_2 = df_modified[df_modified.dirt_rate == "20"].astype(int)
modified_3 = df_modified[df_modified.dirt_rate == "30"].astype(int)

vanilla_0 = df_vanilla[df_vanilla.dirt_rate == "0"].astype(int)
vanilla_1 = df_vanilla[df_vanilla.dirt_rate == "10"].astype(int)
vanilla_2 = df_vanilla[df_vanilla.dirt_rate == "20"].astype(int)
vanilla_3 = df_vanilla[df_vanilla.dirt_rate == "30"].astype(int)



x0 = modified_0["down_time"]
x1 = vanilla_0["down_time"]
y = np.arange(10) + 1
fig, ax = plt.subplots()    
ax.plot(y, x0, label = "Modified")    
ax.plot(y, x1, label = "Vanilla")    

ax.set_xticks(y)
ax.set_xticklabels(y)

plt.xlabel('Dirty rate')
plt.ylabel('Down Time')

plt.title('Variation of down time for 0% processor speed')
plt.legend()
plt.show()

x0 = modified_1["down_time"]
plt.plot(y, x0, label = "Modified")
x1 = vanilla_1["down_time"]
plt.plot(y, x1, label = "Vanilla")


plt.xlabel('Dirty rate')
plt.ylabel('Down Time')
plt.title('Variation of down time for 10% processor speed')
plt.legend()
plt.show()

x0 = modified_2["down_time"]
plt.plot(y, x0, label = "Modified")
x1 = vanilla_2["down_time"]
plt.plot(y, label = "Vanilla")


plt.xlabel('Dirty rate')
plt.ylabel('Down Time')
plt.title('Variation of down time for 20% processor speed')
plt.legend()
plt.show()

x0 = modified_3["down_time"]
plt.plot(np.arange(10)+1, x0, label = "Modified")
x1 = vanilla_3["down_time"]
plt.plot(y, x1, label = "Vanilla")


plt.xlabel('Dirty rate')
plt.ylabel('Down Time')
plt.title('Variation of down time for 30% processor speed')
plt.legend()
plt.show()




x0 = modified_0["total_time"]
plt.plot(np.arange(10)+1, x0, label = "Modified")
x1 = vanilla_0["total_time"]
plt.plot(np.arange(10)+1, x1, label = "Vanilla")


plt.xlabel('Dirty rate')
plt.ylabel('Total Time')
plt.title('Variation of Total time for 0% processor speed')
plt.legend()
plt.show()

x0 = modified_1["total_time"]
plt.plot(np.arange(10)+1, x0, label = "Modified")
x1 = vanilla_1["total_time"]
plt.plot(np.arange(10)+1, x1, label = "Vanilla")


plt.xlabel('Dirty rate')
plt.ylabel('Total Time')
plt.title('Variation of Total time for 10% processor speed')
plt.legend()
plt.show()

x0 = modified_2["total_time"]
plt.plot(np.arange(10)+1, x0, label = "Modified")
x1 = vanilla_2["total_time"]
plt.plot(np.arange(10)+1, x1, label = "Vanilla")


plt.xlabel('Dirty rate')
plt.ylabel('Total Time')
plt.title('Variation of Total time for 20% processor speed')
plt.legend()
plt.show()


x0 = modified_3["total_time"]
plt.plot(np.arange(10)+1, x0, label = "Modified")
x1 = vanilla_3["total_time"]
plt.plot(np.arange(10)+1, x1, label = "Vanilla")


plt.xlabel('Dirty rate')
plt.ylabel('Total Time')
plt.title('Variation of Total time for 30% processor speed')
plt.legend()
plt.show()


x0 = [modified_0.mean()[2],modified_1.mean()[2],modified_2.mean()[2]]
x1 = [vanilla_0.mean()[2],vanilla_1.mean()[2],vanilla_2.mean()[2]]
Y = x0
Z = x1
X = np.arange(3)*10

fig, ax = plt.subplots()    

ax.bar(X - 1.25, Y, color = 'b', width = 2.5, label = "Modified")
ax.bar(X + 1.25, Z, color = 'g', width = 2.5, label = "Vanilla")

ax.set_xticks(X)
ax.set_xticklabels(('0%', '10%', '20%'))

plt.xlabel('Dirty Rate')
plt.ylabel('Downtime Time')
plt.title('Variation of downtime time for different dirty rate')
plt.legend()
plt.show()



x0 = [modified_0.mean()[1],modified_1.mean()[1],modified_2.mean()[1]]
x1 = [vanilla_0.mean()[1],vanilla_1.mean()[1],vanilla_2.mean()[1]]
Y = x0
Z = x1
X = np.arange(3)*10


fig, ax = plt.subplots()    

ax.bar(X - 1.25, Y, color = 'b', width = 2.5, label = "Modified")
ax.bar(X + 1.25, Z, color = 'g', width = 2.5, label = "Vanilla")

ax.set_xticks(X)
ax.set_xticklabels(('0%', '10%', '20%'))

plt.xlabel('Dirty rate')
plt.ylabel('Total Time')
plt.title('Variation of Total time for different dirty rate')
plt.legend()
plt.show()


