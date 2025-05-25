from flask import Flask, render_template, request, send_file, redirect, url_for
import os
import pandas as pd
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'output'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

def is_valid_mavach(mavach):
    if pd.isna(mavach):
        return False
    mavach_str = str(mavach).strip()
    return mavach_str.isdigit() and len(mavach_str) == 13

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        data_file = request.files.get("data_file")
        maufile_file = request.files.get("maufile_file")

        if not data_file or not maufile_file:
            return render_template("index.html", message="Vui lòng chọn đủ cả 2 file.")

        data_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(data_file.filename))
        maufile_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(maufile_file.filename))

        data_file.save(data_path)
        maufile_file.save(maufile_path)

        try:
            data = pd.read_excel(data_path)
            maufile = pd.read_excel(maufile_path)

            data['Mã vạch'] = data['Mã vạch'].apply(
                lambda x: str(int(x)).strip() if pd.notna(x) and isinstance(x, (int, float)) else str(x).strip()
            )
            maufile['Mã vạch'] = maufile['Mã vạch'].apply(lambda x: str(x).strip())

            data['Tên hàng'] = data['Tên hàng'].str.strip()
            maufile['Tên hàng'] = maufile['Tên hàng'].str.strip()

            mavach_to_mahang = data[data['Mã vạch'].apply(is_valid_mavach)].set_index('Mã vạch')['Mã hàng'].to_dict()
            tenhang_to_mahang = data.set_index('Tên hàng')['Mã hàng'].to_dict()

            def get_mahang(row):
                mavach = row['Mã vạch']
                if is_valid_mavach(mavach):
                    mahang_mapped = mavach_to_mahang.get(mavach)
                    if mahang_mapped:
                        return mahang_mapped
                tenhang = row['Tên hàng']
                return tenhang_to_mahang.get(tenhang, None)

            maufile['Mã hàng'] = maufile.apply(get_mahang, axis=1)

            output_filename = "output_result.xlsx"
            output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
            maufile.to_excel(output_path, index=False)

            return redirect(url_for("download", filename=output_filename))

        except Exception as e:
            return render_template("index.html", message=f"Có lỗi xảy ra: {e}")

    return render_template("index.html")

@app.route("/download/<filename>")
def download(filename):
    return send_file(os.path.join(app.config['OUTPUT_FOLDER'], filename), as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
