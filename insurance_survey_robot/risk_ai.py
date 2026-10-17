TRAIN = [
    (0, 48, 'NORMAL'), (1, 54, 'NORMAL'), (2, 59, 'NORMAL'),
    (17, 82, 'FLOOD_RISK'), (20, 91, 'FLOOD_RISK'), (15, 88, 'FLOOD_RISK'),
]


def predict(water_cm, humidity):
    """3-NN: pick 3 closest labeled examples, vote for the majority label."""
    distances = []
    for train_water, train_humidity, label in TRAIN:
        # Scale both features so that one unit of measurement won't dominate.
        d = ((water_cm - train_water) / 20) ** 2 + ((humidity - train_humidity) / 100) ** 2
        distances.append((d, label))
    nearest = sorted(distances)[:3]
    labels = [label for _, label in nearest]
    return max(set(labels), key=labels.count)


if __name__ == '__main__':
    assert predict(18, 90) == 'FLOOD_RISK'
    assert predict(1, 52) == 'NORMAL'
    print('AI test OK: 18cm/90% -> FLOOD_RISK; 1cm/52% -> NORMAL')
