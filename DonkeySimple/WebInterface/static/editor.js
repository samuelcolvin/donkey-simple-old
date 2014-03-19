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

// receive response from form ajax submit
function fajax_response(response_text){
	hide_all();
	if (typeof(response_text.success) != 'undefined')
		message_fade(response_text.success, 'success');
	if (typeof(response_text.errors) != 'undefined'){
		message_fade(response_text.errors, 'danger');
		if (typeof(response_text.info) != 'undefined')
			message_fade(response_text.info, 'info');		
	}
	if (typeof(response_text.warnings) != 'undefined')
		message_fade(response_text.warnings, 'warning');
}
function fajax_error(data){
	console.log(data);
	hide_all();
	var jdata = JSON.parse(data.responseText);
	var errors = [jdata.error, jdata.error_name];
	message_fade(errors, 'danger');
}
function hide_all(){
	$('.alert-success').hide();
	$('.alert-danger').hide();
	$('.alert-info').hide();
	$('.alert-warning').hide();
}
function message_fade(msg, msg_class){
	var el_name = '.alert-' + msg_class;
	var el = $(el_name);
	el.show();
	el.html('<p>' + msg.join('</p>\n<p>') + '</p>');
	if (msg_class == 'success')
		setTimeout("$('" + el_name + "').fadeOut()", 2000);
}

// submit ajax form => save and generate
$('#fajax').click(function() {
	update_code_tb();
	$('[name="function"]').val($(this).attr('save_gen_func'));
    $('#form').ajaxSubmit({
	    success: fajax_response,
	    url: json_submit_url,
	    dataType: 'json',
	    error: fajax_error,
	}); 
    return false; 
}); 

// catch ctrl+s and cmd+s and save
$(document).ready(function(){
	if ($('.save_shortcut').length > 0){
		Mousetrap.bind(['command+s', 'ctrl+s'], function(e) {
		    $('.save_shortcut').click();
		    return false;
		});
		$.each(editors, function(){
			this.editor.commands.addCommand({
			    bindKey: {win: "Ctrl-s", mac: "Command-s"},
			    exec: function() { $('.save_shortcut').click(); }
			});
		});
	}
});
