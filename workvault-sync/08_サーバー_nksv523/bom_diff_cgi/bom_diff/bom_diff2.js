// index.cgiのためのjavascript
// 結果のダウンロード
function dlFile(scrn) {
	var content = ""; 
	var filename = "";
	var myTbl = "";
	if (scrn == 'index'){
		filename = "sabun.csv";
		myTbl = document.getElementById('tablstr');
		// ファイル内容の生成
		for(var j = 1 ; j <= myTbl.rows.length - 2 ; j++){				//trの数だけループ(表題欄含まず)
			content = content + myTbl.rows[j].cells[0].innerText + "," ;	//指図
			content = content + myTbl.rows[j].cells[1].innerText + "," ;	//担当
			content = content + "'" + myTbl.rows[j].cells[2].innerText + "'," ;	//品目コード
			content = content + myTbl.rows[j].cells[3].innerText + "," ;	//台数
			content = content + myTbl.rows[j].cells[4].innerText + "," ;	//指図登録日
			content = content + myTbl.rows[j].cells[5].innerText + "," ;	//製造開始日
			content = content + myTbl.rows[j].cells[6].innerText + "," ;	//完成予定日
			content = content + myTbl.rows[j].cells[7].innerText + "," ;	//タイプ
			if (myTbl.rows[j].cells[8].innerHTML.match(/red/)) {
				content = content + "NG" ;							//差分あり
			}else if (myTbl.rows[j].cells[8].innerHTML.match(/blu/)) {
				content = content + "DONE" ;						//差分修正済
			}else if (myTbl.rows[j].cells[8].innerHTML.match(/grn/)) {
				content = content + "OK" ;							//差分なし
			}
			content = content + "\r\n" ;
		}
	}else if (scrn == 'sashizu'){
		filename = document.getElementById('sashizu').innerText + ".csv";
		myTbl = document.getElementById('sashizu_t');
		// ファイル内容の生成
		content = content + document.getElementById('sashizu').innerText + "," ;
		content = content + document.getElementById('typeID').innerText + "," ;
		content = content + document.getElementById('qty').innerText + "\r\n" ;
		for(var j = 1 ; j <= myTbl.rows.length - 2 ; j++){				//trの数だけループ(表題欄含まず)
			content = content + "'" + myTbl.rows[j].cells[0].innerText + "'," ;	//品目コード
			content = content + myTbl.rows[j].cells[1].innerText + "," ;		//BOSS基数
			content = content + myTbl.rows[j].cells[2].innerText ;				//EGPro基数
			content = content + "\r\n";
		}
	}
	var blob = new Blob([content], { "type" : "text/plain" });
	// ブラウザで処理を分岐
	if (window.navigator.msSaveBlob) { 
		// IEの場合
		//window.navigator.msSaveBlob(blob, filename); 		// ファイルを"保存"
		window.navigator.msSaveOrOpenBlob(blob, filename);	// ファイルを"保存"or"開く"
	}else{
		// IE以外の場合
		var url = window.URL.createObjectURL(blob);
		// 仮想的に"a"要素を生成
		const a = document.createElement("a");
		document.body.appendChild(a);
		a.style = "display:none";
		a.href = url;
		a.download = filename;
		a.click();							// clickをシミュレートして自動ダウンロード
		window.URL.revokeObjectURL(url); 	// release the used object.
		a.parentNode.removeChild(a); 		// delete the temporary "a" element
	}
}
//　差分結果のフィルタリング
function selSabun(col) {
	// checkboxの状態を取得
	const btn_grn = document.getElementById("chkGrn").checked ;
	const btn_red = document.getElementById("chkRed").checked ;
	const btn_blu = document.getElementById("chkBlu").checked ;
	const btn_wht = document.getElementById("chkWht").checked ;
	const btn_NA = document.getElementById("chkNA").checked ;
	// 行の表示/非表示を選択
	const myTbl = document.getElementById('tablstr');
	// ファイル内容の生成
	for(var j = 1 ;j <= myTbl.rows.length - 2 ; j++){				//trの数だけループ(表題欄含まず)
		if (myTbl.rows[j].cells[8].innerHTML.match(/grn/)) {
			if (btn_grn == false){
				myTbl.rows[j].style.display = "none" ;
			}else{
				myTbl.rows[j].style.display = "" ;
			}
		}else if (myTbl.rows[j].cells[8].innerHTML.match(/red/)) {
			if (btn_red == false){
				myTbl.rows[j].style.display = "none" ;
			}else{
				myTbl.rows[j].style.display = "" ;
			}
		}else if (myTbl.rows[j].cells[8].innerHTML.match(/blu/)) {
			if (btn_blu == false){
				myTbl.rows[j].style.display = "none" ;
			}else{
				myTbl.rows[j].style.display = "" ;
			}
		}else if (myTbl.rows[j].cells[8].innerHTML.match(/wht/)) {
			if (btn_wht == false){
				myTbl.rows[j].style.display = "none" ;
			}else{
				myTbl.rows[j].style.display = "" ;
			}
		}else if (myTbl.rows[j].cells[8].innerText.match(/N\.A\./)) {
			if (btn_NA == false){
				myTbl.rows[j].style.display = "none" ;
			}else{
				myTbl.rows[j].style.display = "" ;
			}
		}
	}
}

// sashizu.cgiのためのjavascript
// 「変更」ボタンの押下による変更先欄の表示
function chgPlant() {
	var selectPlant = document.getElementById('chgBtn') ;
	selectPlant.insertAdjacentHTML('afterend',
	'　場所名：<input type="text" size="10" name="new_plant">' + 
	'<input type="submit" name="chgplant" value="登録">' + 
	'<br>注）BOSS品目、基数で登録されます。' );
}
//　差分結果のフィルタリング
function selSabun2() {
	// checkboxの状態を取得
	const box_diff = document.getElementById("diff").checked ;
	// 行の表示/非表示を選択
	const myTbl = document.getElementById('sashizu_t');
	// 表示有無の設定
	for(var j = 1 ;j <= myTbl.rows.length - 2 ; j++){				// trの数だけループ(表題欄含まず)
		if (box_diff == true){
			if (myTbl.rows[j].cells[0].innerHTML.match(/<b>/)) {	// cells[0]に太字の<b>有無を目印
				myTbl.rows[j].style.display = "" ;					
			}else{
				myTbl.rows[j].style.display = "none" ;
			}
		}else{
			myTbl.rows[j].style.display = "" ;
		}
	}
}
