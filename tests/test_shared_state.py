import threading


def test_defaults_are_auto(state):
    assert state.analogue_gain == 0.0
    assert state.colour_temperature == 0
    assert state.consume_shutter_request() is False  # no request pending


def test_consume_resets_request(state):
    state.request_shutter()
    assert state.consume_shutter_request() is True
    assert state.consume_shutter_request() is False


def test_one_request_is_consumed_exactly_once(state):
    state.request_shutter()
    results = []
    start = threading.Barrier(8)

    def worker():
        start.wait()
        results.append(state.consume_shutter_request())

    threads = [threading.Thread(target=worker) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert results.count(True) == 1
