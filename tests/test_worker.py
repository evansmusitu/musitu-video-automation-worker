from worker import manual_balance_observation, test_local_playback as verify_local_playback


def test_manual_balance_is_not_payout_proof():
    result = manual_balance_observation(0, 2.5)
    assert result["displayed_balance_change_usd"] == 2.5
    assert result["payout_independently_verified"] is False


def test_manual_balance_decrease():
    assert manual_balance_observation(8, 7)["displayed_balance_change_usd"] == -1


def test_owned_video_actually_plays():
    result = verify_local_playback(1.5)
    assert result["result"] == "pass", result
    assert result["elapsed_media_seconds"] >= 0.5
    assert result["third_party_paid_views_generated"] == 0
