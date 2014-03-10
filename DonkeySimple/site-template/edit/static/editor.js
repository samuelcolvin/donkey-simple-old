// change action for alternative submit buttons
$('[type=submit]').click(function(){
	var action = $(this).attr('altaction');
	if (typeof(action) != 'undefined'){
		$('[name="action"]').val(action);
	}
});

// generic editor setup
var editors = [];
function setup_editor(ace_id, format){
	console.log('Changing #' + ace_id + ' ace div to format: "' + format + '"');
	var editor = ace.edit(ace_id);
	if (format != ''){
		var mode = require(format).Mode;
		editor.getSession().setMode(new mode());
	}
	editor.setShowPrintMargin(false);
	editor.getSession().setUseWrapMode(true);
	editors.push({editor:editor, div:$('#' + ace_id)});
}

// generic update textbox function
$('#form').on('submit', update_code_tb);
function update_code_tb(){
	$.each(editors, function(){
		var escaped_text = $('#blank').text(this.editor.getValue()).html();
		$('[name="' + this.div.attr('tb_name') + '"]').val(escaped_text);
	});
}

// setup the editor when there is one #editor item - eg file editor
function setup_with_extension(){
	var format = '';
	var ext = $('[name="file-name"]').val().split('.').pop();
	var formats = ['html', 'js', 'json', 'css', 'md'];
	if ($.inArray(ext, formats) != -1){
		if (ext == 'js')
			ext = 'javascript';
		if (ext == 'md')
			ext = 'markdown';
		format = 'ace/mode/' + ext;
	}
	setup_editor('editor', format);
}
if ($('#editor').length > 0){
	setup_with_extension();
	$('[name="file-name"]').change(setup_with_extension);
}

// setup each editor when there are multiple
function get_dropdown(t){
	return $('[name="' + $(t).attr('format-type-input') + '"]');
}
function setup_from_dropdown(d){
	var ace_id = $(d).attr('id');
	var format = get_dropdown(d).val();
	format = 'ace/mode/' + format;
	setup_editor(ace_id, format);
}
$.each($('.ace-editor'), function(){
	setup_from_dropdown(this);
	get_dropdown(this).change(function(){
		console.log(this);
		var editor_attr = $(this).attr('name');
		var div = $('[format-type-input=' + editor_attr + ']');
		console.log(div);
		setup_from_dropdown(div);});
});

// specific warning function for change of template
$('[name="page-template-id"].warn-change').change(function(){
	bootbox.confirm('Changing the template may involve changing the fields of this page, fields missing from the new Template will be deleted!',
	function(result) {
	  if (result){
	  	$('#form').attr('action', '');
	  	$('#form').submit();
	  }
	  else{
	  	$('[name="page-template"]').val($('[name="original-template"]').val());
	  }
	});
});
