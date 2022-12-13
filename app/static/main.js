// $(document).ready(function() {

// 	//E-mail Ajax Send
// 	$("form").submit(function() { //Change
// 		var th = $(this);
// 		$.ajax({
// 			type: "POST",
// 			url: "/telegram", //Change
// 			data: th.serialize()
// 		}).done(function() {
// 			alert("Thank you!");
// 			setTimeout(function() {
// 				// Done Functions
// 				th.trigger("reset");
// 			}, 1000);
// 		});
// 		return false;
// 	});

// });


$(document).ready(function() {
	$('form').on('submit', function(event) {
	  $.ajax({
		 data : {
			Name : $('#Name').val(),
			Telegram: $('#Telegram').val(),
			msg_text: $('#msg_text').val(),
				},
			type : 'POST',
			url : '/telegram'
		   })
	   .done(function(data) {
		setTimeout(function() {
				// Done Functions
				th.trigger("reset");
			}, 1000);
		 $('#output').text(data.output).show();
		 $('#Name').val('');
		 $('#Telegram').val('');
		 $('#msg_text').val('');
	 });
	 event.preventDefault();
	 });
});