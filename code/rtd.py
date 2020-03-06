"""
rtd.py
------

Attempt at an implementation of the rank turbulence divergence, which
was recently introduced in the following paper:

Dodds, P.S.,  Minot, J. R., Arnold, M. V., Alshaabi, T., Adams, J. L.,
Dewhurst, D. R., Gray, T. J., Frank, M. R., Reagan, A. J., Danforth C. M.
(2020). Allotaxonometry and rank-turbulence divergence: A universal instrument
for comparing complex systems. on arXiv.

link to arXiv paper: https://arxiv.org/abs/2002.09770

author: Brennan Klein
email: brennanjamesklein at gmail dot com

"""

import numpy as np
from collections import Counter
import itertools as it
from scipy.stats import rankdata


def get_combined_domain(X1, X2):
    """
    Returns a list of the unique elements in two list-like objects. Note that
    there's a lot of ways to make this function, but given how the rest of the
    rank-turbulence divergence function is structured, it's nice to have this
    self-contained version.

    Parameters
    ----------
    X1, X2 (list or np.ndarray or dict):
        Two list-like objects with domains that need to be joined.

    Returns
    -------
    combined_domain (list):
        List of unique elements in the two inputs.

    """

    if type(X1) == dict:
        domain1 = list(X1.keys())
    else:
        domain1 = list(X1)

    if type(X2) == dict:
        domain2 = list(X2.keys())
    else:
        domain2 = list(X2)

    combined_domain = list(set(domain1 + domain2))

    return combined_domain


def get_rank_dictionary(X, C):
    """
    Returns a dictionary where the keys are the items being ranked and the
    values are their corresponding ranks, using fractional rankings.

    Parameters
    ----------
    X (list or np.ndarray or dict):
        Either a list of raw data (which will need to be counted and reshaped)
        or a dictionary of {element:counts} or a rank-ordered list of elements.
        See the documentation for rank_turbulence_divergence for more details
        about what types of inputs should be provided.

    C (dict):
        Empty dictionary to be populated by counts, then ranked.

    Returns
    -------
    R (dict):
        dict where the keys are the ranked elements and the values are their
        fractional ranking.

    N (int):
        Number of unique elements in X.

    """

    if type(X) == dict:
        dtype_dict = True
        N = len(set(list(X.keys())))
        c = X.copy()
    else:
        dtype_dict = False
        N = len(set(list(X)))

    if not dtype_dict:
        if len(np.unique(X)) == len(X):
            m = list(range(len(X)))
            aug = [[v] * (m[len(m) - i - 1] + 1) for i, v in enumerate(X)]
            x = list(it.chain.from_iterable(aug))
            c = dict(Counter(x))

        else:
            c = dict(Counter(X))

    for k, v in c.items():
        C[k] += v

    d = list(C.keys())
    counts = list(C.values())

    # strange step, but scipy's ranking function is reversed
    ranking = len(counts) - rankdata(counts) + 1
    R = dict(zip(d, ranking))

    return R, N


def rank_turbulence_divergence(X1, X2, alpha=1.0):
    r"""
    Calculates the rank turbulence divergence between two ordered rankings,
    $R_1$ and $R_2$. This is done via the following equation, with a tunable
    ``inverse temperature'' parameter, alpha.

    $ D_{\alpha}^{R}(R_1||R_2) =
        \dfrac{1}{\mathcal{N}_{1,2;\alpha}}
        \dfrac{\alpha+1}{\alpha}
        \sum_{\tau \in R_{1,2;\alpha}}
            \Big\vert \dfrac{1}{\big[r_{\tau,1}\big]^\alpha} -
            \dfrac{1}{\big[r_{\tau,2}\big]^\alpha} \Big\vert^{1/(\alpha+1)} $

    where The $\mathcal{N}_{1,2,\alpha}$ term refers to a normalization factor
    that forces the rank-turbulence divergence between 0 and 1, as follows:

    $ \mathcal{N}_{1,2;\alpha} =
        \dfrac{\alpha+1}{\alpha}
        \sum_{\tau \in R_1}
        \Big\vert \dfrac{1}{\big[r_{\tau,1}\big]^\alpha} -
        \dfrac{1}{\big[N_1+\frac{1}{2}N_2\big]^\alpha} \Big\vert^{1/(\alpha+1)}
        + \dfrac{\alpha+1}{\alpha} \sum_{\tau \in R_1} \Big\vert
        \dfrac{1}{\big[N_2 + \frac{1}{2}N_1\big]^\alpha} -
        \dfrac{1}{\big[r_{\tau,2}\big]^\alpha} \Big\vert^{1/(\alpha+1)} $

    where $N_1$ and $N_2$ are the sizes of $R_1$ and $R_2$ (i.e. the number)
    of things being ranked.

    Parameters
    ----------
    X1, X2 (list or np.ndarray, or dict):
        Two rank-ordered vectors, that do not need to be of the same domain. It
        admits the following datatypes:

            1) X1 = ['mary','jane','chelea','ann'],
               X2 = ['ann','jane','barb','crystal']

               ...as two already-ranked lists of $\tau$s. In X1, then, 'mary'
               would be in rank position 1.0, 'jane' in 2.0, etc.

            2) X1 = ['mary','mary','mary','mary','mary','mary','jane','jane',
                     'jane','chelsea','chelsea','barb']
               X2 = ['ann','ann','ann','ann','ann','jane','jane','jane',
                     'jane','barb','barb','crystal']

                ...as two "raw" datasets, without pre-counting the number of
                elements in each list. Ultimately, in X1, 'mary' shows up 6
                timees, 'jane' shows up 3 times, 'chelsea' shows up 2 times,
                and 'ann' shows up once. This function transforms this input
                data into a dictionary of counts, then ultimately a dictionary
                of ranks, such that $R_1$ and $R_2$ vectors for this example
                are the same as in the first example.

            3) X1 = {'mary':6, 'jane':3, 'chelsea':2, 'ann':1}
               X2 = {'ann':5, 'jane':4, 'barb':2, 'crystal':1}

               ...as two dictionaries of {tau:count}. This might be useful in
               a setting where you're given, for example, vote counts (i.e.,
               {'Bernie Sanders':4000, 'Joseph Biden':2000, ... etc}).


    alpha (float):
        Tuning parameter, acts like an inverse temperature, such that a higher
        value will ``zoom in'' on the data, making small deviations appear very
        important to the final ranking. alpha ranges from 0 to infinity.

    Returns
    -------
    Q (float):
        The rank turbulence divergence between $R_1$ and $R_2$, a scalar
        value between 0 and 1.

    """

    combined_domain = get_combined_domain(X1, X2)
    C1 = {i: 0 for i in combined_domain}
    C2 = {i: 0 for i in combined_domain}

    # Turn both vectors into dictionaries where the key is $\tau$, the property
    # that's being ranked (popular baby names, sports teams, etc.), and the
    # values are their (fractional) rank. This is gonna be useful when we loop
    # through all $\tau$s in order to calculate the rank turbulence divergence.
    R1, N1 = get_rank_dictionary(X1, C1)
    R2, N2 = get_rank_dictionary(X2, C2)

    # Then we're gonna be using certain terms frequently, so might as well
    # turn those values into their own variables and give them useless names.
    alph_exp = 1 / (alpha+1)
    alph_mul = (alpha+1) / alpha
    normN1 = (N1 + 0.5 * N2)**(-alpha)
    normN2 = (N2 + 0.5 * N1)**(-alpha)

    # as we loop through the elements in combined_domain, we'll be gradually
    # adding to these numbers.
    norm_1 = 0
    norm_2 = 0
    Q = 0

    for tau in combined_domain:
        r1tau_exp_negalpha = R1[tau]**(-alpha)
        r2tau_exp_negalpha = R2[tau]**(-alpha)
        dQ = np.abs(r1tau_exp_negalpha - r2tau_exp_negalpha)

        norm_1 += np.abs(r1tau_exp_negalpha - normN1)**alph_exp
        norm_2 += np.abs(normN2 - r2tau_exp_negalpha)**alph_exp

        Q += dQ**alph_exp

    Cr = alph_mul * norm_1 + alph_mul * norm_2
    Q = 1/Cr * alph_mul * Q

    return Q


def main():
    """Empty main function."""
    return


if __name__ == '__main__':
    main()
