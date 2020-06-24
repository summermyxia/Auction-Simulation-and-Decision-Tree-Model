import bisect

def turnbull(data, interval_length = float('inf'), bins = [], low_price = 0, high_price = -1, num_bins = 1000, epsilon = 0.01):
    if not bins:
        if high_price == -1:
            high_price = max([k[0] for k in data])
        
        intervals = []
        for price, win in data:
            intervals.append((max(price - interval_length, low_price), price) if win else (price, min(price + interval_length, high_price)))
        
        bins = [low_price]
        bin_width = (high_price - low_price) / num_bins
        for _ in range(num_bins - 1):
            bins.append(bins[-1] + bin_width)
        bins = bins[1:]
    else:
        num_bins = len(bins) + 1
        low_price = bins[0] * 2 - bins[1]
        high_price = bins[-1] * 2 - bins[-2]
    
    alpha = []
    for left, right in intervals:
        left_idx = bisect.bisect_left(bins, left)
        right_idx = bisect.bisect_left(bins, right)
        alpha.append([left_idx, right_idx])

    density = [1 / num_bins for _ in range(num_bins)]
    diff = float('inf')
    n, m = len(data), num_bins
    while diff > epsilon:
        denominators = []
        for i in range(n):
            denominators.append(sum([density[j] for j in range(alpha[i][0], alpha[i][1] + 1)]))
        
        newdensity = [0] * num_bins
        for i in range(n):
            if denominators[i] != 0:
                for j in range(alpha[i][0], alpha[i][1] + 1):
                    newdensity[j] += density[j] / denominators[i]
        for j in range(m):
            newdensity[j] /= n

        diff = sum([abs(newdensity[j] - density[j]) for j in range(m)])
        density = newdensity

    x = [bins[0] * 2 - bins[1]] + bins
    dist = [density[0]]
    for k in density[1:]:
        dist.append(dist[-1] + k)

    return x, dist