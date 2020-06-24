import bisect

def turnbull(data, interval_length = 3, low_price = 0, high_price = -1, num_bins = 1000, epsilon = 0.001):
    if high_price == -1:
        high_price = max([k[0] for k in data])
    
    intervals = []
    for price, win in data:
        intervals.append((price, min(price + interval_length, high_price)) if win else (max(price - interval_length, low_price), price))
    
    bins = [low_price]
    bin_width = (high_price - low_price) / num_bins
    for _ in range(num_bins - 1):
        bins.append(bins[-1] + bin_width)
    bins = bins[1:]
    
    alpha = []
    for left, right in intervals:
        new_alpha_row = [0 for _ in range(num_bins)]
        left_idx = bisect.bisect_left(bins, left)
        right_idx = bisect.bisect_left(bins, right)
        new_alpha_row[left_idx:(right_idx + 1)] = [1] * (right_idx - left_idx + 1)
        alpha.append(new_alpha_row)

    density = [1 / num_bins for _ in range(num_bins)]
    diff = float('inf')
    n, m = len(alpha), len(alpha[0])
    while diff > epsilon:
        denominators = []
        for i in range(n):
            denominators.append(sum([alpha[i][j] * density[j] for j in range(m)]))
        
        newdensity = []
        for j in range(m):
            value = 0
            for i in range(n):
                if denominators[i] != 0:
                    value += alpha[i][j] * density[j] / denominators[i]
            value /= n
            newdensity.append(value)
            # newdensity.append(sum([(alpha[i][j] * density[j] / denominators[i]) if denominators[i] != 0 else 0 for i in range(n)]) / n)

        diff = sum([abs(newdensity[j] - density[j]) for j in range(m)])
        density = newdensity

    x = [bins[0] * 2 - bins[1]] + bins
    dist = [density[0]]
    for k in density[1:]:
        dist.append(dist[-1] + k)

    return x, dist