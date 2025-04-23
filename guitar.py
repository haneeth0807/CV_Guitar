import cv2
from cvzone.HandTrackingModule import HandDetector
import pygame.midi
import time
import threading

pygame.midi.init()
player = pygame.midi.Output(0)
player.set_instrument(25)

cap = cv2.VideoCapture(0)
detector = HandDetector(detectionCon=0.8, maxHands=2)

chords = {
    "thumb":  [45, 52, 57, 60, 64, 69],        # Am
    "index":  [43, 47, 50, 55, 59, 62],        # G
    "middle": [48, 52, 55, 60, 64],            # C (skip low E)
    "ring":   [41, 45, 50, 53, 57, 60],        # F
    "pinky":  [40, 47, 52, 55, 59, 64]         # Em
}

right_finger_names = ["thumb", "index", "middle", "ring", "pinky"]
left_finger_names = ["index", "pinky"]
left_finger_indices = {"index": 1, "pinky": 4}

active_chord = None
prev_right_state = {f: 0 for f in right_finger_names}
prev_left_state = {f: 0 for f in left_finger_names}

note_timestamps = {}

def strum(chord_notes, direction="down", delay=0.02, sustain=2.0):
    if direction == "up":
        chord_notes = list(reversed(chord_notes))

    now = time.time()
    this_strum_notes = []

    for note in chord_notes:
        if note is not None:
            player.note_on(note, 127)
            note_timestamps[note] = now 
            this_strum_notes.append(note)
            time.sleep(delay)

    def stop_notes():
        time.sleep(sustain)
        for note in this_strum_notes:
            if note_timestamps.get(note) == now:
                player.note_off(note, 127)

    threading.Thread(target=stop_notes, daemon=True).start()

while True:
    success, img = cap.read()
    if not success:
        print("Failed to capture frame.")
        continue

    hands, img = detector.findHands(img)

    right_hand, left_hand = None, None
    for hand in hands:
        if hand["type"] == "Right":
            right_hand = hand
        elif hand["type"] == "Left":
            left_hand = hand

    if right_hand:
        fingers = detector.fingersUp(right_hand)
        for i, finger in enumerate(right_finger_names):
            if fingers[i] == 1 and prev_right_state[finger] == 0:
                active_chord = chords[finger]
                print(f"Selected chord: {finger} → {active_chord}")
            prev_right_state[finger] = fingers[i]

    if left_hand and active_chord:
        fingers = detector.fingersUp(left_hand)
        if fingers[4] == 1 and prev_left_state["pinky"] == 0:
            print("Strum down")
            strum(active_chord, "down")
        prev_left_state["pinky"] = fingers[4]

        if fingers[1] == 1 and prev_left_state["index"] == 0:
            print("Strum up")
            strum(active_chord, "up")
        prev_left_state["index"] = fingers[1]        
    else:
        prev_left_state = {f: 0 for f in left_finger_names}

    cv2.imshow("Virtual Guitar", img)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
pygame.midi.quit()
