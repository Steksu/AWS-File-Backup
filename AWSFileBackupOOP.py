from tkinter import filedialog, StringVar
import customtkinter as ctk
from tkinterdnd2 import TkinterDnD, DND_ALL
from CTkListbox import *
from CTkMessagebox import CTkMessagebox
import boto3
import botocore
import os
import threading

class Tk(ctk.CTk, TkinterDnD.DnDWrapper):

    def __init__(self, access_key_id, secret_access_key, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.TkdndVersion = TkinterDnD._require(self)

        self.geometry("800x600")
        self.title("AWS File Manager")
        self.mode = "dark"
        
        self.s3 = boto3.resource('s3',
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key)
        self.bucket_name = 'awsmainbucket1'
        self.filenames = set()

        top_frame = ctk.CTkFrame(self)
        top_frame.pack(fill="x", padx=10, pady=10)

        self.entryWidget_text_var = ctk.StringVar(value="Drag and drop file in the entry box")
        self.entryWidget = ctk.CTkEntry(top_frame, state='readonly', corner_radius=15, width=550, height=150, textvariable=self.entryWidget_text_var, justify='center')
        self.entryWidget.pack(padx=50, pady=20)
        self.entryWidget.drop_target_register(DND_ALL)
        self.entryWidget.dnd_bind("<<Drop>>", self.get_path)

        self.pathLabel = ctk.CTkLabel(top_frame, text="Drag and drop file in the entry box")
        self.pathLabel.pack()

        left_frame = ctk.CTkFrame(self)
        left_frame.pack(side="left", fill="y", padx=10, pady=10)

        self.choose_file_button = ctk.CTkButton(left_frame, text="Choose Files", command=self.choose_files)
        self.choose_file_button.pack(pady=15)

        self.listbox_chosen_files = CTkListbox(left_frame, width=150)
        self.listbox_chosen_files.pack(pady=(0, 10))
        self.clear_files_button = ctk.CTkButton(left_frame, text="Clear files", command=self.delete_chosen_files)
        self.clear_files_button.pack()

        self.theme_button = ctk.CTkSwitch(left_frame, text="Change theme", command=self.dark_theme)
        self.theme_button.pack(side = "bottom", pady= 10)

        self.upload_button = ctk.CTkButton(left_frame, text="Upload Files", command=lambda: self.upload_files(self.filenames), height= 50)
        self.upload_button.pack(side = "bottom", pady=5)

        center_frame = ctk.CTkFrame(self)
        center_frame.pack(side="left", expand=True, fill="both", padx=10, pady=10)

        self.entry_search_var = StringVar()
        
        self.search_widget = ctk.CTkEntry(center_frame, placeholder_text="Search Files", textvariable=self.entry_search_var, width=200)
        self.search_widget.pack(pady=10)
        self.search_widget.bind("<Return>", lambda event: self.search_filter(self.entry_search_var.get()))

        self.listbox = CTkListbox(center_frame, multiple_selection=True, width=550, height = 150)
        self.listbox.pack(expand=True, padx=10, pady=0)

        self.files_in_bucket = self.get_file_names()

        self.listbox_items = []
        for i, filename in enumerate(self.files_in_bucket):
            if filename:
                self.listbox.insert(i, f"{filename}")
                self.listbox_items.append(f"{filename}")


        self.download_button = ctk.CTkButton(center_frame, text="Download Files", command=lambda: self.download_files(self.listbox.get()))
        self.download_button.pack(pady=5)

        print(sorted(self.listbox_items))

        self.progress_bar = ctk.CTkProgressBar(center_frame, orientation="horizontal", height=20, corner_radius=0, border_width=2, width=500, progress_color="aquamarine")
        self.progress_bar.pack(pady = (20,0))
        self.progress_bar.set(0)

        self.progress_bar_text = ctk.CTkLabel(center_frame, text="Upload progress")
        self.progress_bar_text.pack(pady = (0,10))

        self.bytes_sent_sum = 0

    def choose_files(self):
        self.progress_bar.set(0)
        self.progress_bar_text.configure(text = f"Upload progress")
        self.filenames.update(set(filedialog.askopenfilenames()))
        for file in self.filenames:
            self.listbox_chosen_files.insert("end", file.split('/')[-1] )
        print(self.filenames)


    def get_path(self, event):

        file_paths = self.tk.splitlist(event.data)

        for path in file_paths:
            path = path.strip('{}')
            print(f"File dropped: {path}")
            self.filenames.update({path})
            self.listbox_chosen_files.insert("end", path.split('/')[-1])

        self.progress_bar.set(0)
        self.progress_bar_text.configure(text = f"Upload progress")
        print(self.filenames)
    

    def delete_chosen_files(self):
        self.filenames = set()
        self.listbox_chosen_files.delete(0, "end")
        
    def progress_callback(self, bytes_sent, total_bytes):
        if total_bytes == 0:
            print("Uploaded: 0/0 bytes (Total bytes is 0)")
            return
        self.bytes_sent_sum += bytes_sent
        print(f"Uploaded: {self.bytes_sent_sum}/{total_bytes} bytes")
        progress_percentage = self.bytes_sent_sum/total_bytes * 100
        self.progress_bar_text.configure(text = f"Upload progress: {round(progress_percentage,2)} %")
        self.progress_bar.set(self.bytes_sent_sum / total_bytes)
        self.update_idletasks()

        if self.bytes_sent_sum == total_bytes:
            self.bytes_sent_sum = 0
            print("Files uploaded")
            self.filenames = set()
            self.listbox_chosen_files.delete(0, "end")
            CTkMessagebox(title="", message="Files uploaded successfully!", icon="check", option_1="OK")
            return
        
    def upload_files(self, file_names):
        total_size = sum(os.path.getsize(filename) for filename in file_names)
        
        for filename in file_names:
            key = 'awsfilebackupfolder/' + filename.split('/')[-1] 
            print(key)
            threading.Thread(target=self.upload_file_with_callback, args=(filename, key, total_size)).start()


    def upload_file_with_callback(self, filename, key, total_size):
        bucket = self.s3.Bucket(self.bucket_name)
        try:
            bucket.upload_file(filename, key, Callback=lambda sent: self.progress_callback(sent, total_size))
        except botocore.exceptions.ClientError as e:
            CTkMessagebox(title="Error", message=str(e), icon="cancel")
        except Exception as e:
            CTkMessagebox(title="Error", message=f"Upload failed! {str(e)}", icon="cancel")

     
    def get_file_names(self):
        bucket = self.s3.Bucket(self.bucket_name)
        files_in_bucket = [f.key.split("awsfilebackupfolder" + "/")[1] for f in bucket.objects.filter(Prefix="awsfilebackupfolder").all()]
        return files_in_bucket

    def download_files(self, file_names):
        print(file_names)
        bucket = self.s3.Bucket(self.bucket_name)

        for filename in file_names:
            key = 'awsfilebackupfolder/' + filename
            print(key)
            file_path = filedialog.asksaveasfilename(initialfile=filename)
            if file_path:
                try:
                    bucket.download_file(key, file_path)
                except botocore.exceptions.ClientError as e:
                    if e.response['Error']['Code'] == "404":
                        CTkMessagebox(title="Error", message="Object does not exist!", icon="cancel")
                    else:
                        CTkMessagebox(title="Error", message=str(e), icon="cancel")
                except Exception as e:
                    CTkMessagebox(title="Error", message=f"Download failed! {str(e)}", icon="cancel")

    def dark_theme(self):
        if self.mode == "dark":
            ctk.set_appearance_mode("light")
            self.mode = "light"
        else:
            ctk.set_appearance_mode("dark")
            self.mode = "dark"
    
    def search_filter(self, sv):
        total_items = self.listbox.size()

        for index in range(total_items):
            self.listbox.deactivate(index)

        self.listbox.delete(0, "end") 
        entry = sv.strip() 
        if entry: 
            matches = [filename for filename in self.listbox_items if entry.lower() in filename.lower()]
            for filename in matches:
                self.listbox.insert("end", filename)
        else:
            for filename in self.listbox_items:
                self.listbox.insert("end", filename)


class KeyValidation(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.TkdndVersion = TkinterDnD._require(self)

        self.geometry("800x600")
        self.title("AWS File Manager")

        self.access_key_label = ctk.CTkLabel(self, text="Access Key ID:")
        self.access_key_label.pack(pady=(200, 5))

        self.access_key_entry = ctk.CTkEntry(self, width = 250)
        self.access_key_entry.pack()

        self.secret_key_label = ctk.CTkLabel(self, text="Secret Access Key:")
        self.secret_key_label.pack()

        self.secret_access_key_entry = ctk.CTkEntry(self, show="*", width = 250)
        self.secret_access_key_entry.pack()

        self.submit_button = ctk.CTkButton(self, text="Submit", command = lambda: self.authenticate())
        self.submit_button.pack(padx=10, pady=20)

        
    def authenticate(self):

        access_key_id = self.access_key_entry.get()
        secret_access_key = self.secret_access_key_entry.get()

        try:
            s3 = boto3.resource('s3', aws_access_key_id=access_key_id, aws_secret_access_key=secret_access_key)
            list(s3.buckets.all())

            self.open_dashboard(access_key_id, secret_access_key)

        except Exception as e:
            CTkMessagebox(title="Warning Message!", message=str(e), icon="warning", option_1="Cancel")

    def open_dashboard(self, access_key_id, secret_access_key):
        self.destroy()
        app = Tk(access_key_id, secret_access_key)
        app.mainloop()   



if __name__ == "__main__":

    app_login = KeyValidation()
    app_login.mainloop()
    