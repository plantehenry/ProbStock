import csv
import os


# Ensure the CSV file exists and has the appropriate headers
def initialize_csv(file_path):
    if not os.path.exists(file_path):
        with open(file_path, mode='w', newline='') as file:
            writer = csv.writer(file)
            # Initialize the CSV with headers
            writer.writerow(['Simulate', 'Graph'])  # Adjust headers as needed

# Add a value to the first column of the CSV file
def add_value_to_first_column(file_path, value):
    with open(file_path, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([value, ''])  # Empty value for the second column

# Add a value to the second column of the CSV file
def add_value_to_second_column(file_path, value):
    # Read all rows and find the correct row to update
    with open(file_path, mode='r+', newline='') as file:
        reader = csv.reader(file)
        rows = list(reader)
        
        if len(rows) <= 1:
            print("No rows available to update.")
            return
        
        # Update the first available row in the second column
        for row in rows[1:]:  # Skip the header
            if row[1] == '':
                row[1] = value
                break
        else:
            print("All rows are filled. Cannot add more data.")
            return
        
        # Write updated data back to the file
        file.seek(0)
        writer = csv.writer(file)
        writer.writerows(rows)
        file.truncate()


