$(document).ready(function() {
    "use strict";
    var _t = openerp._t;
	var currentUrl = location.href;
	var title = $(document).find("title").text();
	$('.oe_structure').each(function(ev){
        
		var oe_website_sale  = this;
		ChangeUrl(title, currentUrl);
        
        $("#file_browse_btn").click(function () {
			var data = $('input.file_browse').val();
			var $form = $(this).closest('form');
            alert(data);
			$form.find('input[type="file"]').click();
		});
        
		// $(oe_website_sale).on('click', 'a.file_browse_btn', function(){
			// var data = $('input.file_browse').val();
			// var $form = $(this).closest('form');
			// $form.find('input[type="file"]').click();
		// });
        
		// add attachment
        $("#btn_attachment").click(function () {
             $("#file_upload_modal").modal();
        });

		// $(this).on('click', 'a.add-attachment', function(){
            // alert('add attachment')
			// $("#file_upload_modal").modal();
		// });

		// view attachment
		$(oe_website_sale).on('click', 'a.view-attachment', function(){
			$('div.attachment-history').slideDown(500, function(){
				$('a.view-attachment').addClass('hide-attachment').removeClass('view-attachment');
				$('a.hide-attachment').html('&#032;Hide Attachment(s)');
			});
			
		});

		$(oe_website_sale).on('click', 'a.hide-attachment', function(){
			$('div.attachment-history').slideUp(500, function(){
				$('a.hide-attachment').addClass('view-attachment').removeClass('hide-attachment');
				$('a.view-attachment').html('&#032;View Attachment(s)');
			});
			
		});

		//$form.find('input[type="file"]').change( function(){
        $(oe_website_sale).find('input[type="file"]').on('change', function(){
            alert('Call this function');
			var $form = $(this).closest('form');
			var name = $(this)[0].files[0].name;
			if((!name) || name ==='')
			{
				$('button.file_upload_btn').hide().addClass('disabled');
			}
			else
			{
				$('button.file_upload_btn').show().removeClass('disabled');
				$('div#file-upload-name').html('<span class="fa fa-file-o"></span>&#032;'+name);
			}
		});

		$(oe_website_sale).on('click', 'img.upload_hide_window', function(){

			$('div.attachment-history').slideUp(500, function() {
				$('img.upload_hide_window').hide();
			});
		});

		$(oe_website_sale).on('click', 'a#attachment-remove', function(){

			var $tbody = $(this).closest('tbody');
			var attachment_id = parseInt($tbody.find('input[name="attachment-id"]').first().val(),10);
			openerp.jsonRpc("/shop/payment/remove_upload", 'call', 
			{
				'attachment_id': attachment_id
			})
			.then(function (msg) 
			{
				location.reload();
			});
		});

		function getPathFromUrl(url) {
		  return url.split("?")[0];
		}

		function ChangeUrl(title, currentUrl) 
		{
			if (currentUrl.indexOf("/page/contactus") != -1 )
			{
				 var newUrl = getPathFromUrl(currentUrl);
				 var obj = { Title: title, Url: newUrl };
				history.pushState(obj, obj.Title, obj.Url);
			}
		}
	});
});