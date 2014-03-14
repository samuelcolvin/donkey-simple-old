// change action for alternative submit buttons
$('[type=submit]').click(function(){
	var altfunction = $(this).attr('altfunction');
	if (typeof(altfunction) != 'undefined'){
		$('[name="function"]').val(altfunction);
	}
	var altaction = $(this).attr('altaction');
	if (typeof(altaction) != 'undefined'){
		$(this).closest('form').attr("action", altaction);
	}
});

// set textarea to readonly for none override context
function set_vis_override(){
	var textarea = $('#value_' + $(this).attr('custom-field'));
	var hidden = $('#hidden_' + $(this).attr('custom-field'));
	console.log(this);
	textarea.prop("disabled", !this.checked);
	if (!this.checked){
		hidden.val(textarea.val());
		textarea.val('');
	}
	else{
		textarea.val(hidden.val());
	}
}
$('.override-context').click(set_vis_override);
$('.override-context').each(set_vis_override);

// generic editor setup
var editors = [];
var ace_modes;
function setup_editor(ace_id, mode){
	console.log('Changing #' + ace_id + ' ace div to format: "' + mode.name + '"');
	var editor = ace.edit(ace_id);
	editor.getSession().setMode(mode.mode);
	editor.setShowPrintMargin(false);
	editor.getSession().setUseWrapMode(true);
	var ace_div = $('#' + ace_id);
	editors.push({editor:editor, div:ace_div});
	ace_div.show();
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
	ace_modes = ace.require('ace/ext/modelist');
	var fname = $('[name="file-name"]').val();
	var mode = ace_modes.getModeForPath(fname);
	setup_editor('editor', mode);
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
	if (typeof(ace_modes) == 'undefined')
		ace_modes = ace.require('ace/ext/modelist');
	var ace_id = $(d).attr('id');
	var format = get_dropdown(d).val();
	var mode = ace_modes.modesByName[format];
	setup_editor(ace_id, mode);
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
