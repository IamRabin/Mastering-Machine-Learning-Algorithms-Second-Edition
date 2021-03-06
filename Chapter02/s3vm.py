import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

from scipy.optimize import minimize

from sklearn.datasets import make_classification

# Set random seed for reproducibility
np.random.seed(1000)


nb_samples = 100
nb_unlabeled = 50


# Create dataset
X, Y = make_classification(n_samples=nb_samples, n_features=2, n_redundant=0, random_state=1000)
Y[Y==0] = -1
Y[nb_samples - nb_unlabeled:nb_samples] = 0


# Initialize S3VM variables
w = np.random.uniform(-0.1, 0.1, size=X.shape[1])
eta = np.random.uniform(0.0, 0.1, size=nb_samples - nb_unlabeled)
xi = np.random.uniform(0.0, 0.1, size=nb_unlabeled)
zi = np.random.uniform(0.0, 0.1, size=nb_unlabeled)
b = np.random.uniform(-0.1, 0.1, size=1)
C = 1.0


# Stack all variables into a single vector
theta0 = np.hstack((w, eta, xi, zi, b))


# Vectorize the min() function
vmin = np.vectorize(lambda x1, x2: x1 if x1 <= x2 else x2)


def svm_target(theta, Xd, Yd):
    wt = theta[0:2].reshape((Xd.shape[1], 1))

    s_eta = np.sum(theta[2:2 + nb_samples - nb_unlabeled])
    s_min_xi_zi = np.sum(vmin(theta[2 + nb_samples - nb_unlabeled:2 + nb_samples],
                              theta[2 + nb_samples:2 + nb_samples + nb_unlabeled]))

    return C * (s_eta + s_min_xi_zi) + 0.5 * np.dot(wt.T, wt)


def labeled_constraint(theta, Xd, Yd, idx):
    wt = theta[0:2].reshape((Xd.shape[1], 1))

    c = Yd[idx] * (np.dot(Xd[idx], wt) + theta[-1]) + \
        theta[2:2 + nb_samples - nb_unlabeled][idx] - 1.0

    return (c >= 0)[0]


def unlabeled_constraint_1(theta, Xd, idx):
    wt = theta[0:2].reshape((Xd.shape[1], 1))

    c = np.dot(Xd[idx], wt) - theta[-1] + \
        theta[2 + nb_samples - nb_unlabeled:2 + nb_samples][idx - nb_samples + nb_unlabeled] - 1.0

    return (c >= 0)[0]


def unlabeled_constraint_2(theta, Xd, idx):
    wt = theta[0:2].reshape((Xd.shape[1], 1))

    c = -(np.dot(Xd[idx], wt) - theta[-1]) + \
        theta[2 + nb_samples:2 + nb_samples + nb_unlabeled][idx - nb_samples + nb_unlabeled] - 1.0

    return (c >= 0)[0]


def eta_constraint(theta, idx):
    return theta[2:2 + nb_samples - nb_unlabeled][idx] >= 0


def xi_constraint(theta, idx):
    return theta[2 + nb_samples - nb_unlabeled:2 + nb_samples][idx - nb_samples + nb_unlabeled] >= 0


def zi_constraint(theta, idx):
    return theta[2 + nb_samples:2 + nb_samples+nb_unlabeled ][idx - nb_samples + nb_unlabeled] >= 0


if __name__ == '__main__':
    # Show the initial dataset
    sns.set()

    fig, ax = plt.subplots(figsize=(12, 9))

    ax.scatter(X[Y == -1, 0], X[Y == -1, 1], marker='o', s=100, label='Class 0')
    ax.scatter(X[Y == 1, 0], X[Y == 1, 1], marker='^', s=100, label='Class 1')
    ax.scatter(X[Y == 0, 0], X[Y == 0, 1], facecolor='none', edgecolor='#003200', marker='o', s=80, label='Unlabeled')

    ax.set_xlabel(r'$x_0$', fontsize=16)
    ax.set_ylabel(r'$x_1$', fontsize=16)
    ax.grid(True)
    ax.legend(fontsize=16)

    plt.show()

    # Setup all the constraints
    svm_constraints = []

    for i in range(nb_samples - nb_unlabeled):
        svm_constraints.append({
            'type': 'ineq',
            'fun': labeled_constraint,
            'args': (X, Y, i)
        })
        svm_constraints.append({
            'type': 'ineq',
            'fun': eta_constraint,
            'args': (i,)
        })

    for i in range(nb_samples - nb_unlabeled, nb_samples):
        svm_constraints.append({
            'type': 'ineq',
            'fun': unlabeled_constraint_1,
            'args': (X, i)
        })
        svm_constraints.append({
            'type': 'ineq',
            'fun': unlabeled_constraint_2,
            'args': (X, i)
        })
        svm_constraints.append({
            'type': 'ineq',
            'fun': xi_constraint,
            'args': (i,)
        })
        svm_constraints.append({
            'type': 'ineq',
            'fun': zi_constraint,
            'args': (i,)
        })

    # Optimize the objective
    print('Optimizing...')
    result = minimize(fun=svm_target,
                      x0=theta0,
                      constraints=svm_constraints,
                      args=(X, Y),
                      method="COBYLA",
                      tol=0.0001,
                      options={
                          "maxiter": 5000,
                      })

    # Extract the last parameters
    theta_end = result['x']
    w = theta_end[0:2]
    b = theta_end[-1]

    Xu = X[nb_samples - nb_unlabeled:nb_samples]
    yu = -np.sign(np.dot(Xu, w) + b)

    # Show the final plots
    fig, ax = plt.subplots(1, 2, figsize=(22, 9), sharey=True)

    ax[0].scatter(X[Y == -1, 0], X[Y == -1, 1], marker='o', s=100, label='Class 0')
    ax[0].scatter(X[Y == 1, 0], X[Y == 1, 1], marker='^', s=100, label='Class 1')
    ax[0].scatter(X[Y == 0, 0], X[Y == 0, 1], facecolor='none', edgecolor='#003200', marker='o', s=100,
                  label='Unlabeled')

    ax[0].set_xlabel(r'$x_0$', fontsize=16)
    ax[0].set_ylabel(r'$x_1$', fontsize=16)
    ax[0].grid(True)
    ax[0].legend(fontsize=16)

    ax[1].scatter(X[Y == -1, 0], X[Y == -1, 1], c='r', marker='o', s=100, label='Labeled class 0')
    ax[1].scatter(X[Y == 1, 0], X[Y == 1, 1], c='b', marker='^', s=100, label='Labeled class 1')

    ax[1].scatter(Xu[yu == -1, 0], Xu[yu == -1, 1], c='r', marker='s', s=150, label='Unlabeled class 0')
    ax[1].scatter(Xu[yu == 1, 0], Xu[yu == 1, 1], c='b', marker='v', s=150, label='Unlabeled class 1')

    ax[1].set_xlabel(r'$x_0$', fontsize=16)
    ax[1].grid(True)
    ax[1].legend(fontsize=16)

    plt.show()