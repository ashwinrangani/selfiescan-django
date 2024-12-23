import pickle

encodings_file = '/home/ashwin/project-django/selfiescan/photoapp/encodings.pkl'

with open(encodings_file, 'rb') as f:
    data = pickle.load(f)
    print(f"Number of encodings: {len(data['encodings'])}")
    print(f"Sample identity: {data['identities'][0] if data['identities'] else 'No identities'}")

