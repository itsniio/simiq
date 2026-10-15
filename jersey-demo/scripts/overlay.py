import sys, numpy as np, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
W="/tmp/claude-0/jersey/work/"
V=np.load(W+"anny_a20.npy"); V[:,2]-=V[:,2].min()
A=np.load(W+"avatar_v.npy")
s=np.array([float(x) for x in sys.argv[1].split(",")]); t=np.array([float(x) for x in sys.argv[2].split(",")])
B=A*s+t
fig,ax=plt.subplots(1,2,figsize=(12,9))
for i,(a,b) in enumerate(((0,2),(1,2))):
    ax[i].scatter(V[::3,a],V[::3,b],s=0.5,c="k"); ax[i].scatter(B[::6,a],B[::6,b],s=0.5,c="r"); ax[i].set_aspect("equal")
plt.savefig(W+"overlay.png",dpi=80)
