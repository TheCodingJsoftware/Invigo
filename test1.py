import math
from sympy import gamma
import time


def partition(n, m):
    """
    The function `partition` generates all possible partitions of a positive integer `n` into `m` parts.

    Args:
      n: The parameter `n` represents the number that we want to partition. It is the number that we
    want to break down into smaller parts.
      m: The parameter `m` represents the number of parts we want to partition `n` into.
    """
    if m == 1:
        yield (n,)
    else:
        for i in range(n + 1):
            for j in partition(n - i, m - 1):
                yield (i,) + j


def E(zeta, epsilon, z):
    """
    The function `E` calculates the value of a mathematical expression involving factorials, partitions,
    and the gamma function.

    Args:
      zeta: The parameter `zeta` is a list of integers.
      epsilon: The parameter `epsilon` is a constant value that is added to the sum of the products of
    `zeta` and `l_partition`. It is used as an input to the gamma function in the calculation of the
    result.
      z: The parameter `z` is a list of values.

    Returns:
      the value of the variable "result".
    """
    m = len(zeta)
    result = 0
    factorials = [math.factorial(i) for i in range(max(zeta) + 1)]  # Cache the factorial values

    for l in range(40):  # approximate upper bound
        for l_partition in partition(l, m):
            if all(map(lambda x: x >= 0, l_partition)):
                combination = 1
                for i in range(m):
                    combination *= factorials[l_partition[i]]  # Use the precomputed factorials
                combination = factorials[l] // combination  # Use integer division for combinations
                gaminput = sum(zeta[i] * l_partition[i] for i in range(m)) + epsilon
                numerator = 1
                for i in range(m):
                    numerator *= z[i] ** l_partition[i]
                result += numerator / math.gamma(gaminput) * combination
    return result


def ME(M, z):  # Matrix Mittag-Leffler function
    """
    The function `ME` calculates the Matrix Mittag-Leffler function for a given matrix `M` and a vector
    `z`.

    Args:
      M: The parameter M is a matrix, represented as a list of lists. Each inner list represents a row
    of the matrix, and the outer list represents the entire matrix. The matrix can have any number of
    rows and columns.
      z: The parameter `z` is a list of complex numbers.

    Returns:
      the value of the Matrix Mittag-Leffler function for the given matrix M and vector z.
    """
    m = len(M)
    zl = len(z)
    result = 0
    for l in range(25):  # approximate upper bound
        for l_partition in partition(l, zl):
            if all(map(lambda x: x >= 0, l_partition)):
                combination = 1
                for i in range(zl):
                    combination *= math.factorial(l_partition[i])
                combination = math.factorial(l) / combination
                gamproduct = 1
                for i in range(m):
                    gaminput = sum(M[i][j] * l_partition[j] for j in range(zl)) + M[i][zl]
                    gamproduct *= gamma(gaminput)
                numerator = 1
                for i in range(zl):
                    numerator *= z[i] ** l_partition[i]
                result += (numerator / gamproduct) * combination
    return result


def main():
    M1 = [
        [0, 0.5, 0.5, 0, 0.5, 0.5, 0.7, 0.5, 0.5, 0.7, 0.5, 0.5, 0, 1.5],
    ]
    z = [0]
    for i in range(5):

        start_time = time.time()

        result1 = ME(M1, z)

        end_time = time.time()
        execution_time = end_time - start_time

        print(f"Result: {result1}")
        print(f"Execution time: {execution_time} seconds")
        z.append(i)


if __name__ == "__main__":
    main()
