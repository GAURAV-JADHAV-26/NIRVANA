@app.route('/save_selected_artists', methods=['POST'])
def save_selected_artists():
    data = request.json
    session['selected_artists'] = data['artists']
    print(session['selected_artists'])
    return jsonify(success=True)