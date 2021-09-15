# To add a new cell, type '# %%'
# To add a new markdown cell, type '# %% [markdown]'
# %%
f_modified = open("./modified.out")
f_vanilla = open("./vanilla.out")


# %%
import re
import numpy as np


# %%
Lines = f_vanilla.readlines()
list_vanilla = []
count = 0
i = 0
for line in Lines:
    count += 1
    pattern = '\d+'
    result = re.findall(pattern, line)
    if i%3 == 0:
        list_vanilla.append([result[0]])
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
        list_modified.append([result[0]])
    else:
        list_modified[int(i/3)].append(result[0])

    i = i+1


    


# %%
import pandas as pd


# %%
df_vanilla = pd.DataFrame.from_records(list_vanilla)
df_modified = pd.DataFrame.from_records(list_modified)
df_vanilla
df_modified


# %%
import matplotlib.pyplot as plt


# %%
df_vanilla.columns = ['dirt_rate', 'total_time', 'down_time']
df_modified.columns = ['dirt_rate', 'total_time', 'down_time']


# %%
modified_0 = df_modified[df_modified.dirt_rate == "512"].astype(int)
modified_1 = df_modified[df_modified.dirt_rate == "1024"].astype(int)
modified_2 = df_modified[df_modified.dirt_rate == "2048"].astype(int)
modified_3 = df_modified[df_modified.dirt_rate == "4096"].astype(int)
modified_4 = df_modified[df_modified.dirt_rate == "8192"].astype(int)

vanilla_0 = df_vanilla[df_vanilla.dirt_rate == "512"].astype(int)
vanilla_1 = df_vanilla[df_vanilla.dirt_rate == "1024"].astype(int)
vanilla_2 = df_vanilla[df_vanilla.dirt_rate == "2048"].astype(int)
vanilla_3 = df_vanilla[df_vanilla.dirt_rate == "4096"].astype(int)
vanilla_4 = df_vanilla[df_vanilla.dirt_rate == "8192"].astype(int)


# %%
x0 = modified_0["down_time"]
plt.plot(np.arange(5)+1, x0, label = "Modified")
x1 = vanilla_0["down_time"]
plt.plot(np.arange(5)+1, x1, label = "Vanilla")


plt.xlabel('VM Size')
plt.ylabel('Down Time')
plt.title('Variation of down time for 512MB VM')
plt.legend()
plt.show()

x0 = modified_1["down_time"]
plt.plot(np.arange(5)+1, x0, label = "Modified")
x1 = vanilla_1["down_time"]
plt.plot(np.arange(5)+1, x1, label = "Vanilla")


plt.xlabel('VM Size')
plt.ylabel('Down Time')
plt.title('Variation of down time for 1024MB VM')
plt.legend()
plt.show()

x0 = modified_2["down_time"]
plt.plot(np.arange(5)+1, x0, label = "Modified")
x1 = vanilla_2["down_time"]
plt.plot(np.arange(5)+1, x1, label = "Vanilla")


plt.xlabel('VM Size')
plt.ylabel('Down Time')
plt.title('Variation of down time for 2048MB VM')
plt.legend()
plt.show()


x0 = modified_3["down_time"]
plt.plot(np.arange(5)+1, x0, label = "Modified")
x1 = vanilla_3["down_time"]
plt.plot(np.arange(5)+1, x1, label = "Vanilla")


plt.xlabel('VM Size')
plt.ylabel('Down Time')
plt.title('Variation of down time for 4096MB VM')
plt.legend()
plt.show()


x0 = modified_4["down_time"]
plt.plot(np.arange(5)+1, x0, label = "Modified")
x1 = vanilla_4["down_time"]
plt.plot(np.arange(5)+1, x1, label = "Vanilla")


plt.xlabel('VM Size')
plt.ylabel('Down Time')
plt.title('Variation of down time for 8192MB VM')
plt.legend()
plt.show()


# %%
x0 = modified_0["total_time"]
plt.plot(np.arange(5)+1, x0, label = "Modified")
x1 = vanilla_0["total_time"]
plt.plot(np.arange(5)+1, x1, label = "Vanilla")


plt.xlabel('VM Size')
plt.ylabel('Total Time')
plt.title('Variation of Total time for 512MB VM')
plt.legend()
plt.show()

x0 = modified_1["total_time"]
plt.plot(np.arange(5)+1, x0, label = "Modified")
x1 = vanilla_1["total_time"]
plt.plot(np.arange(5)+1, x1, label = "Vanilla")


plt.xlabel('VM Size')
plt.ylabel('Total Time')
plt.title('Variation of Total time for 1024MB VM')
plt.legend()
plt.show()


x0 = modified_2["total_time"]
plt.plot(np.arange(5)+1, x0, label = "Modified")
x1 = vanilla_2["total_time"]
plt.plot(np.arange(5)+1, x1, label = "Vanilla")


plt.xlabel("VM Size")
plt.ylabel('Total Time')
plt.title('Variation of Total time for 2048MB VM')
plt.legend()
plt.show()


x0 = modified_3["total_time"]
plt.plot(np.arange(5)+1, x0, label = "Modified")
x1 = vanilla_3["total_time"]
plt.plot(np.arange(5)+1, x1, label = "Vanilla")


plt.xlabel("VM Size")
plt.ylabel('Total Time')
plt.title('Variation of Total time for 4096MB VM')
plt.legend()
plt.show()


x0 = modified_4["total_time"]
plt.plot(np.arange(5)+1, x0, label = "Modified")
x1 = vanilla_4["total_time"]
plt.plot(np.arange(5)+1, x1, label = "Vanilla")


plt.xlabel("VM Size")
plt.ylabel('Total Time')
plt.title('Variation of Total time for 8192MB VM')
plt.legend()
plt.show()


# %%

x0 = [
    modified_0.mean()[2],
    modified_1.mean()[2],
    modified_2.mean()[2],
    modified_3.mean()[2],
    modified_4.mean()[2]
    ]
x1 = [
    vanilla_0.mean()[2],
    vanilla_1.mean()[2],
    vanilla_2.mean()[2],
    vanilla_3.mean()[2],
    vanilla_4.mean()[2]
    ]
Y = x0
Z = x1
X = np.arange(5)* 1024

fig, ax = plt.subplots()    
ax.bar(X - 128, Y, color = 'b', width = 256, label = "Modified")
ax.bar(X + 128, Z, color = 'g', width = 256, label = "Vanilla")


ax.set_xticks(X)
ax.set_xticklabels(('512', '1024', '2048', '4096', '8192'))

plt.xlabel('VM Size')
plt.ylabel('Downtime Time')
plt.title('Variation of downtime time for different VM Size')
plt.legend()
plt.show()


# %%

x0 = [
    modified_0.mean()[1],
    modified_1.mean()[1],
    modified_2.mean()[1],
    modified_3.mean()[1],
    modified_4.mean()[1]
    ]
x1 = [
    vanilla_0.mean()[1],
    vanilla_1.mean()[1],
    vanilla_2.mean()[1],
    vanilla_3.mean()[1],
    vanilla_4.mean()[1]
    ]
Y = x0
Z = x1
X = np.arange(5)* 1024

fig, ax = plt.subplots()    
ax.bar(X - 128, Y, color = 'b', width = 256, label = "Modified")
ax.bar(X + 128, Z, color = 'g', width = 256, label = "Vanilla")


ax.set_xticks(X)
ax.set_xticklabels(('512', '1024', '2048', '4096', '8192'))

plt.xlabel('VM Size')
plt.ylabel('Total Time')
plt.title('Variation of total time for different VM size')
plt.legend()
plt.show()


