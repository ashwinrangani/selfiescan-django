import face_recognition
import os
import pickle

base_dir = os.path.dirname(os.path.abspath(__file__))
dataset_path = os.path.join(base_dir, '..', 'media', 'dataset')


encodings_file = os.path.join(base_dir, 'encodings.pkl')

encodings = []
identities = []

for img_file in os.listdir(dataset_path):
    img_path = os.path.join(dataset_path, img_file)
    image = face_recognition.load_image_file(img_path)
    enc = face_recognition.face_encodings(image)

    if enc:
        encodings.append(enc[0])
        # Store relative path instead of full path
        relative_path = os.path.relpath(img_path, os.path.join(base_dir, 'media'))
        identities.append(relative_path)
        print(relative_path)


# Save encodings and identities
with open(encodings_file, 'wb') as f:
    pickle.dump({'encodings': encodings, 'identities': identities}, f)
print("Encodings saved to", encodings_file)



