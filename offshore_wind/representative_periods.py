import numpy as np


def bin_division(TS, n_bins, N_total, n_div):
    # Calculate minimum bin values
    bin_mn = [i for i in range(n_bins)]

    # Normalize the input time series
    TS = TS / max(TS)

    # Compute values for the entire time series (TS)
    A_o = np.empty([n_bins, 1], dtype=object)
    for ii in range(n_bins):
        logic = sum(sum(TS > bin_mn[ii]))
        A_o[ii] = logic / len(TS)

    # Compute values for each period in the time series (TS)
    A = np.empty([n_bins, N_total], dtype=object)
    for ii in range(N_total):
        if ii > 0:
            ts = TS[[ii] * n_div:[ii] * n_div + (n_div - 1)]  # CHECK THIS ONE...
        else:
            ts = TS[1:n_div - 1]
        for jj in range(n_bins):
            logic = sum(sum(ts > bin_mn[jj]))
            A[jj, ii] = logic / n_div

    return A_o, A


def HYB_day_opt(TS, N_repr, N_total, N_subsets, n_bins, n_div=24):
    # Example usage from matlab:
    # LOAD -- time series comes directly from NYISO data
    # N_repr = 24  (numbe of time periods per day)
    # N_total = 365 (number of days)
    # N_subsets = 10 (number of subsets ???)
    # n_bins = 10 (number of bins ???)
    # D, w_d = HYB_day_opt(LOAD, N_repr, N_total, N_subsets, n_bins)

    # Initialize the arrays for speed
    d = np.empty([N_repr, N_subsets], dtype=object)
    w = np.empty([N_repr, N_subsets], dtype=object)
    error = np.empty([1, N_subsets], dtype=object)
    A = np.empty([n_bins, N_repr], dtype=object)

    for ii in range(N_subsets):
        # Randomly select numbers between 1 and N_total and avoid repeats
        D = np.random.randint(0, N_total, size=(N_repr, 1))
        while np.sum(np.sum(d) == np.sum(D)) > 0:
            D = np.random.randint(0, N_total, size=(N_repr, 1))
        d[:, ii] = D

        # Compute A_{c, b, d} for all days and exctract the parameter for chosen days
        L, A_all = bin_division(TS, n_bins, N_total, n_div)
        for jj in range(N_repr):
            A[:, jj] = A_all[:, D[jj]]

        # Run the optimization model (original CVX code here as a stand-in)
        # cvx_begin quiet
        #     variable
        #     w_d(N_repr, 1)
        #     minimize(sum(abs(L - A * (w_d / N_total))))
        #     subject to
        #         w_d >= 0;
        #         sum(w_d) == N_total;
        # cvx_end

        # Store the error and w_d values
        w[:, ii] = w_d
        error[ii] = cvx_optval

    # Extract d and w_d pair corresponding to the lowest error metric value
    [_, loc] = np.min(error)
    D = d[:, loc]
    w_d = w[:, loc]


if __name__ == "__main__":

