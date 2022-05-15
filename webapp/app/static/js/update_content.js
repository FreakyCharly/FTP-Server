/**
 *  Update content.
 */
function update(){
    $.ajax({
        type : 'POST',
        url : "/banner",
        success: function(result){
            $("#banner").text('Current users online: ' + result.banner)
        }
    });
}