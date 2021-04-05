import matplotlib
import matplotlib.pyplot as plt

plt.plot([0, 1, 2, 3, 4], [0, 3, 5, 9, 11])
plt.xlabel('Time')
plt.ylabel('Price')
plt.savefig('graph.png')