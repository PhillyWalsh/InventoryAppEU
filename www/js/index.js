var app = {
    // Application Constructor
    initialize: function() {
        this.bindEvents();
    },
    // Bind Event Listeners
    //
    // Bind any events that are required on startup. Common events are:
    // 'load', 'deviceready', 'offline', and 'online'.
    bindEvents: function() {
        document.addEventListener('deviceready', this.onDeviceReady, false);
    },
    // deviceready Event Handler
    //
    // The scope of 'this' is the event. In order to call the 'receivedEvent'
    // function, we must explicity call 'app.receivedEvent(...);'
    onDeviceReady: function() {
        app.receivedEvent('deviceready');
    },
    // Update DOM on a Received Event
    receivedEvent: function(id) {
        var parentElement = document.getElementById(id);

        console.log('Received Event: ' + id);
    }
};

app.initialize();

var title = "";
var author = "";
var price = "";
var secondCategory = "";
var pic = "";



document.addEventListener("offline", onOffline, false);

function onOffline() {
    alert("No Internet Connection!");
}




function startScan() {
    cordova.plugins.barcodeScanner.scan(
        function (result) {
            window.scanned_barcode = result.text;
            APICall(result.text);
        }, 
        function (error) {
            var result = document.getElementById("result");
            result.innerHTML = "Scanning failed: " + error;
        }
    );
};

var pictureSource;   // picture source
var destinationType; // sets the format of returned value
 
document.addEventListener("deviceready", onDeviceReady, false);
 
function onDeviceReady() {
    pictureSource = navigator.camera.PictureSourceType;
    destinationType = navigator.camera.DestinationType;
}
 
function clearCache() {
    navigator.camera.cleanup();
}

 
function onCapturePhoto(fileURI) {
 
    var options = new FileUploadOptions();
    options.fileKey = "file";
    options.fileName = fileURI.substr(fileURI.lastIndexOf('/') + 1);
    options.mimeType = "image/jpeg";
    options.params = {}; // if we need to send parameters to the server request
    options.chunkedMode = true;
    var ft = new FileTransfer();
    console.log(fileURI);
    ft.upload(fileURI, encodeURI("http://inventoryapp.eu/upload/"), 
            function(success){
                clearCache();
                console.log(success.response);
                console.log("Code = " + success.responseCode);
                console.log("Sent = " + success.bytesSent);
                var ocr = success.response.trim();
                console.log(localStorage.getItem("fid"));
                $('#'+localStorage.getItem("fid")).val(ocr);
            }, 
            function(error){
                clearCache();
                console.log(error.code);
                console.log(error.source);
                console.log(error.target);
                console.log(error);
                var ocr = error.trim();
            }, 
            options
    );
}
 
function capturePhoto() {
    navigator.camera.getPicture(onCapturePhoto, onFail, {
        quality: 100,
        destinationType: destinationType.FILE_URI,
        targetWidth: 459,
        targetheight: 816
    });
}
 
function onFail(message) {
    alert('Failed because: ' + message);
}

function getOcr() {
    var result = localStorage.getItem("ocr");
    localStorage.setItem("ocr", "");
    return result;
}

function exportItems(){
    var json_data = userIdJson();
    $.support.cors = true;
    $.ajax({
        type: 'POST',
        url: 'http://178.62.87.155/export/',
        data: JSON.stringify (json_data),
        contentType: "application/json; charset=utf-8",
        dataType: 'json',
        success: function(data) {
            console.log(data)
             var details = data.collection[0];
            if(details.result =="Sent")
                {
                     $('#report-action').html("<b>Report sent to: </b><i>"+ details.email +"</i>");
                }
            else if(details.result =="Not Sent")
                {
                    $('#report-action').html("<b>Error email not sent</b>");
                }
            else{
                alert("error")
            };
            
        },
        error: function(xhr, status, error){
          console.log(xhr);
          console.log(status);
          console.log(error);
      }
    });
}


  
function addItemMan(){
    scanned_barcode = document.getElementById("barcode-input").value;
    title = document.getElementById("input-title").value;
    price = document.getElementById("input-price").value;
    secondCategory = document.getElementById("input-category").value;
    pic = "http://178.62.87.155/static/images/question-mark.png";
    var json_data = createItemJson();
     $.support.cors = true;
     $.ajax({
        type: 'POST',
        url: 'http://178.62.87.155/table/post/items/',
        data: JSON.stringify (json_data),
        contentType: "application/json; charset=utf-8",
        dataType: 'json',
        success: function(data) {
            console.log(data);
            var details = data.collection[0];
            console.log(details.response);
            if(details.response =="item-added")
                {
                    alert("Item Added to Inventory");
                    window.location.href = 'index.html';
                }
            else if(details.response =="item-exist")
                {
                    alert("Item already added/updated on: "+ details.date);
                }
            else {
                alert("Something went wrong");    
            }
        },
        error: function(xhr, status, error){
          console.log(xhr);
          console.log(status);
          console.log(error);
      }
    });
}

function addBookMan(){
    scanned_barcode = document.getElementById("book-input-barcode").value;
    title = document.getElementById("book-input-title").value;
    author = document.getElementById("book-input-author").value;
    price = document.getElementById("book-input-price").value;
    secondCategory = document.getElementById("book-input-cat").value;
    pic = "http://178.62.87.155/static/images/question-mark.png";
    var json_data = createBookJson();
    $.support.cors = true;
    $.ajax({
        type: 'POST',
        url: 'http://178.62.87.155/table/post/books/',
        data: JSON.stringify (json_data),
        contentType: "application/json; charset=utf-8",
        dataType: 'json',
        success: function(data) {
            console.log(data);
            var details = data.collection[0];
            console.log(details.response);
            if(details.response =="item-added")
                {
                    alert("Item Added to Inventory");
                    window.location.href = 'index.html';
                }
            else if(details.response =="item-exist")
                {
                    alert("Item already added/updated on: "+ details.date);
                }
            else {
                alert("Something went wrong");    
            }
        },
        error: function(xhr, status, error){
          console.log(xhr);
          console.log(status);
          console.log(error);
      }
    });
}


function search(text) {
    $('#search-items').empty();
    var searchText = text.toLowerCase().trim();
    $.ajax ({
        type: 'GET',
        dataType: 'json',
        url: 'http://178.62.87.155/app/search/'+ localStorage.getItem("userid") +'/'+ searchText +'/',
        success: function(response){
          console.log(response);
          $('#search-items').html("<li class='table-view-cell media'><i>Items: </i>"+ response.collection.length+"</i></b></li>")
          for(var i = 0; i < response.collection.length; i++) {
              var listing = response.collection[i];
              var threeDigits = listing.barcode.slice(0,3);
              if (threeDigits == "978" || threeDigits == "979") {
                $('#search-items').append("<li class='table-view-cell media' data-code = '"+ listing.barcode +"' data-id = '"+ listing.iid +"' onclick='setId(this)'><a class='navigate-right' transition='slide' href='#'><div class='media-object pull-left'><img style='max-width: 60px;' src='"+ listing.pic_url +"' /></div><div class='media-body'><p style='font-size: 14px;'>"+ listing.title +"</p><p id='itemList'><b id='headings'><i><u>Author:</u></i></b></p><p id='itemList'>"+ listing.author +"</p><p><b id='headings'><i><u>Price:</u></i></b></p><p id='itemList'>&euro;"+ listing.price +"</p></div></a></li>");
              }
              else {
                $('#search-items').append("<li class='table-view-cell media' data-code = '"+ listing.barcode +"' data-id = '"+ listing.iid +"' onclick='setId(this)'><a class='navigate-right' transition='slide' href='#'><div class='media-object pull-left'><img style='max-width: 60px;' src='"+ listing.pic_url +"' /></div><div class='media-body'><p style='font-size: 14px;'>"+ listing.title +"</p><p id='itemList'><b id='headings'><i><u>Category:</u></i></b></p><p id='itemList'>"+ listing.category +"</p><p><b id='headings'><i><u>Price:</u></i></b></p><p id='itemList'>&euro;"+ listing.price +"</p></div></a></li>");
              }
          }
        }, 
        error: function(xhr, status, error){
          console.log(xhr)
          console.log(status);
          console.log(error);
        }
    });
}

function goBack() {
window.history.back();
}

function check_login() {
    if (localStorage.getItem("logged_in") === "null" || localStorage.getItem("logged_in") == "null") {
        // variable is undefined or null
        window.location.href = 'login.html';
    }
}

function logout() {
    localStorage.setItem("logged_in", null);
    localStorage.setItem("userid", null);
    localStorage.setItem("username", null);
    localStorage.setItem("ocr", null);
    window.location.href = 'login.html';
}

function setFieldId(item){
    var fid = item.getAttribute("data-id"); 
    localStorage.setItem("fid", fid);
}

function setId(item){
    var iid = item.getAttribute("data-id");
    var code = item.getAttribute("data-code");
    localStorage.setItem("id", iid);
    localStorage.setItem("barcode", code);
    window.location.href = 'editItem.html';
}

function deleteItem(){
    $.ajax ({
        type: 'DELETE',
        dataType: 'json',
        url: 'http://178.62.87.155/app/delete/'+ localStorage.getItem("id") +'/'+ localStorage.getItem("barcode") +'',
        success: function(response){
            console.log(response);
            alert("Item Deleted")
            localStorage.setItem("id", null);
            localStorage.setItem("barcode", null);
            window.location.href = localStorage.getItem("ppage");
    }, 
    error: function(xhr, status, error){
        console.log(status);
        console.log(error);
  }
    });
}

function setNewTitle(title){
            localStorage.setItem("newTitle", title);
            console.log(localStorage.getItem("newTitle"))
            updateItem();
    }

function updateItem(){
    var json_data = updateTitleJson(); 
    $.ajax ({     
        type: 'PUT',
        dataType: 'json',
        url: 'http://178.62.87.155/app/update/'+ localStorage.getItem("id") +'/'+ localStorage.getItem("barcode") +'',
        data: JSON.stringify (json_data),    
        success: function(response){
            console.log(response);
            alert("Item Updated")
            localStorage.setItem("id", null);
            localStorage.setItem("barcode", null);
            localStorage.setItem("newTitle", null);
            window.location.href = localStorage.getItem("ppage");
  }, 
    contentType: "application/json",
    dataType: 'json',    
    error: function(xhr, status, error){
      console.log(status);
      console.log(error);
  }
    });
}

function getItem(){
    $.ajax ({
        type: 'GET',
    dataType: 'json',
    url: 'http://178.62.87.155/app/showitem/'+ localStorage.getItem("id") +'/'+ localStorage.getItem("barcode") +'/',
    success: function(response){
      console.log(response);
      for(var i = 0; i < response.collection.length; i++) {
          var listing = response.collection[i];
          var threeDigits = localStorage.getItem("barcode").slice(0,3);
          if (threeDigits == "978" || threeDigits == "979") {
            $('#edit-item').html("<div class='editable-item' data-code = '"+ listing.barcode +"' data-id = '"+ listing.iid +"'><div id='item-pic'><center><img style='max-height: 23vh; padding-top: 5px;' src='"+ listing.pic_url +"' /></center></div><div class='edit-body'><textarea name='title-text' id='title-text' rows='2' cols='20'>"+ listing.title +"</textarea><div class='details-content'><p id='itemDetails'><b id='headings'><i>Author:    </i></b>"+ listing.author +"</p><p id='itemDetails'><b id='headings'><i>Category:    </i></b>"+ listing.category +"</p><p id='itemDetails'><b id='headings'><i>Price:    </i></b>&euro;"+ listing.price +"</p><p id='itemDetails'><b id='headings'><i>Added/Modified:    </i></b>"+ listing.ts.slice(0,-7) +"</p></div></div></div>");   
          }
          else {
            $('#edit-item').html("<div class='editable-item' data-code = '"+ listing.barcode +"' data-id = '"+ listing.iid +"'><div id='item-pic'><center><img style='max-height: 23vh; padding-top: 5px;' src='"+ listing.pic_url +"' /></center></div><div class='edit-body'><textarea name='title-text' id='title-text' rows='2' cols='20'>"+ listing.title +"</textarea><div class='details-content'><p id='itemDetails'><b id='headings'><i>Category:    </i></b>"+ listing.category +"</p><p id='itemDetails'><b id='headings'><i>Price:    </i></b>&euro;"+ listing.price +"</p><p id='itemDetails'><b id='headings'><i>Added/Modified:    </i></b>"+ listing.ts.slice(0,-7) +"</p></div></div></div>");
          }
      }
  }, 
    error: function(xhr, status, error){
      console.log(xhr)
      console.log(status);
      console.log(error);
  }
    });
}

function getBooks(){
    $.ajax ({
        type: 'GET',
    dataType: 'json',
    url: 'http://178.62.87.155/app/books/'+ localStorage.getItem("userid") +'',
    success: function(response){
        localStorage.ppage = "bookList.html";
        console.log(response);
        for(var i = 0; i < response.collection.length; i++) {
            var listing = response.collection[i];
            $('#books').append("<li class='table-view-cell media' data-code = '"+ listing.barcode +"' data-id = '"+ listing.iid +"' onclick='setId(this)'><a class='navigate-right' transition='slide' href='#'><div class='media-object pull-left'><img style='max-width: 60px;' src='"+ listing.pic_url +"' /></div><div class='media-body'><p style='font-size: 14px;'>"+ listing.title +"</p><p id='itemList'><b id='headings'><i><u>Author:</u></i></b></p><p id='itemList'>"+ listing.author +"</p><p><b id='headings'><i><u>Price:</u></i></b></p><p id='itemList'>&euro;"+ listing.price +"</p></div></a></li>");
        }
  }, 
    error: function(xhr, status, error){
      console.log(status);
      console.log(error);
  }
    });
}

function getGames(){
    $.ajax ({
        type: 'GET',
    dataType: 'json',
    url: 'http://178.62.87.155/app/games/'+ localStorage.getItem("userid") +'',
    success: function(response){
      console.log(response);
      localStorage.ppage = "gamesList.html";
      for(var i = 0; i < response.collection.length; i++) {
          var listing = response.collection[i];
          $('#games').append("<li class='table-view-cell media' data-code = '"+ listing.barcode +"' data-id = '"+ listing.iid +"' onclick='setId(this)'><a class='navigate-right' transition='slide' href='#'><div class='media-object pull-left'><img style='max-width: 60px;' src='"+ listing.pic_url +"' /></div><div class='media-body'><p style='font-size: 14px;'>"+ listing.title +"</p><p id='itemList'><b id='headings'><i><u>Category:</u></i></b></p><p id='itemList'>"+ listing.category +"</p><p><b id='headings'><i><u>Price:</u></i></b></p><p id='itemList'>&euro;"+ listing.price +"</p></div></a></li>");
      }
  }, 
    error: function(xhr, status, error){
      console.log(status);
      console.log(error);
  }
    });
}

function getDvds(){
    $.ajax ({
        type: 'GET',
    dataType: 'json',
    url: 'http://178.62.87.155/app/dvds/'+ localStorage.getItem("userid") +'',
    success: function(response){
      console.log(response);
      localStorage.ppage = "dvdList.html";
      for(var i = 0; i < response.collection.length; i++) {
          var listing = response.collection[i];
          $('#dvds').append("<li class='table-view-cell media' data-code = '"+ listing.barcode +"' data-id = '"+ listing.iid +"' onclick='setId(this)'><a class='navigate-right' transition='slide' href='#' ><div class='media-object pull-left'><img style='max-width: 60px;' src='"+ listing.pic_url +"' /></div><div class='media-body'><p style='font-size: 14px;'>"+ listing.title +"</p><p id='itemList'><b id='headings'><i><u>Category:</u></i></b></p><p id='itemList'>"+ listing.category +"</p><p><b id='headings'><i><u>Price:</u></i></b></p><p id='itemList'>&euro;"+ listing.price +"</p></div></a></li>");
      }
  }, 
    error: function(xhr, status, error){
      console.log(status);
      console.log(error);
  }
    });
}

function getItems(){
    $.ajax ({
        type: 'GET',
    dataType: 'json',
    url: 'http://178.62.87.155/app/items/'+ localStorage.getItem("userid") +'',
    success: function(response){
      console.log(response);
      localStorage.ppage = "itemList.html";
      for(var i = 0; i < response.collection.length; i++) {
          var listing = response.collection[i];
          $('#items').append("<li class='table-view-cell media' data-code = '"+ listing.barcode +"' data-id = '"+ listing.iid +"' onclick='setId(this)'><a class='navigate-right' transition='slide' href='#'><div class='media-object pull-left'><img style='max-width: 60px;' src='"+ listing.pic_url +"' /></div><div class='media-body'><p style='font-size: 14px;'>"+ listing.title +"</p><p id='itemList'><b id='headings'><i><u>Category:</u></i></b></p><p id='itemList'>"+ listing.category +"</p><p><b id='headings'><i><u>Price:</u></i></b></p><p id='itemList'>&euro;"+ listing.price +"</p></div></a></li>");
      }
  }, 
    error: function(xhr, status, error){
      console.log(status);
      console.log(error);
  }
    });
}


function userIdJson() {

    var json_details = {
                            "template": 
                                {
                                    "data": [
                                                {
                                                    "uid": localStorage.getItem("userid")
                                                }
                                            ]
                                } 
                         }

    return json_details
}

function updateTitleJson() {

    var x = localStorage.getItem("newTitle")
    var title = x.trim()
    var json_details = {
                            "template": 
                                {
                                    "data": [
                                                {
                                                    "title": title
                                                }
                                            ]
                                } 
                         }

    return json_details
}

function createBookJson() {
    var json_details = {
                            "template": 
                                {
                                    "data": [
                                                {
                                                    "uid": localStorage.getItem("userid"),
                                                    "barcode": scanned_barcode,
                                                    "title": title,
                                                    "author": author,
                                                    "category": secondCategory,
                                                    "pic_url": pic,
                                                    "price": price
                                                }
                                            ]
                                } 
                         }
    console.log(json_details);
    return json_details
}

function createItemJson() {
    var json_details = {
                            "template": 
                                {
                                    "data": [
                                                {
                                                    "uid": localStorage.getItem("userid"),
                                                    "barcode": scanned_barcode,
                                                    "title": title,
                                                    "category": secondCategory,
                                                    "pic_url": pic,
                                                    "price": price
                                                }
                                            ]
                                } 
                         }

    return json_details
}

function createUser(username, email, password) {
    var json_details = {
                            "template": 
                                {
                                    "data": [
                                                {
                                                    "username": username,
                                                    "email": email,
                                                    "password": password
                                                }
                                            ]
                                } 
                         }

    return json_details
}

function loginUser(username, password) {
    var json_details = {
                            "template": 
                                {
                                    "data": [
                                                {
                                                    "username": username,
                                                    "password": password
                                                }
                                            ]
                                } 
                         }

    return json_details
}


function _cb_GetSingleItem(root) {

    author = "Unknown";
    var itemSpec = root.Item.ItemSpecifics.NameValueList;
    for(var i = 0; i < itemSpec.length; i++) {
        if (itemSpec[i].Name == "Author") {

            author = itemSpec[i].Value.toString();  
            console.log(author);
        }
    }

    console.log(author);
    sendBookDetails();

}

function sendBookDetails(){
    var json_data = createBookJson();
    $.support.cors = true;
    $.ajax({
        type: 'POST',
        url: 'http://178.62.87.155/table/post/books/',
        data: JSON.stringify (json_data),
        contentType: "application/json; charset=utf-8",
        dataType: 'json',
        success: function(data) {
            console.log(data);
            var details = data.collection[0];
            console.log(details.response);
            if(details.response =="item-added")
                {
                    $('#scanAction').html("<b>Item Added to Inventory</b>");
                }
            else if(details.response =="item-exist")
                {
                    $('#scanAction').html("<b>Item already added/updated on: </b><br><i>"+ details.date +"</i>");
                }
            else {
                alert("Something went wrong");    
            }
        },
        error: function(xhr, status, error){
          console.log(xhr);
          console.log(status);
          console.log(error);
      }
    });
    $('#lastScanned').html("<ul class='table-view'><li class='table-view-cell media'><div class='media-object pull-left'><img style='max-width: 60px;' src='"+ pic +"' /></div><div class='media-body'><p>"+ title +"</p><p><b><i><u>Author:</u></i></b></p><p>"+ author +"</p><p><b><i><u>Price:</u></i></b></p><p>&euro;"+ price +"</p></div></a></li></ul>");
}

function _cb_findItemsAdvanced(root) {
    if (root.findItemsAdvancedResponse[0].paginationOutput[0].totalEntries == 0) {
        alert("No Item found!")
    }
    else {
        var item = root.findItemsAdvancedResponse[0].searchResult[0].item[0] || [];
        title    = item.title.toString();
        price = Number(item.sellingStatus[0].convertedCurrentPrice[0].__value__).toFixed(2);
        secondCategory = item.primaryCategory[0].categoryName.toString();
        var ebayId = item.itemId;
        try{
            pic = item.galleryURL[0];  
        }
        catch(err){
            console.log(err);
            pic = "http://178.62.87.155/static/images/question-mark.png";
        }
        var threeDigits = scanned_barcode.slice(0,3);
        if (threeDigits == "978" || threeDigits == "979") {

            var url = "http://open.api.ebay.com/shopping?";
            url += "callname=GetSingleItem&";
            url += "responseencoding=JSON&";
            url += "appid=Philipwa-6547-4a99-bb7f-42bceb8c89eb&";
            url += "siteid=0&";
            url += "version=515&";
            url += "IncludeSelector=ItemSpecifics&";
            url += "ItemID="+ ebayId +"&";
            url += "callbackname=_cb_GetSingleItem";

            // Submit the request 
            s=document.createElement('script'); // create script element
            s.src= url;
            document.body.appendChild(s);

        } 
        else {
            var json_data = createItemJson();
             $.support.cors = true;
             $.ajax({
                type: 'POST',
                url: 'http://178.62.87.155/table/post/items/',
                data: JSON.stringify (json_data),
                contentType: "application/json; charset=utf-8",
                dataType: 'json',
                success: function(data) {
                    console.log(data);
                    var details = data.collection[0];
                    console.log(details.response);
                    if(details.response =="item-added")
                        {
                            $('#scanAction').html("<b>Item Added to Inventory</b>");
                        }
                    else if(details.response =="item-exist")
                        {
                            $('#scanAction').html("<b>Item already added/updated on: </b><br><i>"+ details.date +"</i>");
                        }
                    else {
                        alert("Something went wrong");    
                    }
                },
                error: function(xhr, status, error){
                  console.log(xhr);
                  console.log(status);
                  console.log(error);
              }
            });
            $('#lastScanned').html("<ul class='table-view'><li class='table-view-cell media'><div class='media-object pull-left'><img style='max-width: 60px;' src='"+ pic +"' /></div><div class='media-body'><p>"+ title +"</p><p><b><i><u>Category:</u></i></b></p><p>"+ secondCategory +"</p><p><b><i><u>Price:</u></i></b></p><p>&euro;"+ price +"</p></div></a></li></ul>");
        }
    }
};  

function APICall(barcode) {

    var filterarray = [
      {"name":"ListingType", 
       "value":["FixedPrice"],
       "paramName":"", 
       "paramValue":""},
      {"name":"Condition", 
       "value":["New"],
       "paramName":"", 
       "paramValue":""},
      ];


var urlfilter = "";

function  buildURLArray() {
  for(var i=0; i<filterarray.length; i++) {
    var itemfilter = filterarray[i];
    for(var index in itemfilter) {
      if (itemfilter[index] !== "") {
        if (itemfilter[index] instanceof Array) {
          for(var r=0; r<itemfilter[index].length; r++) {
          var value = itemfilter[index][r];
          urlfilter += "&itemFilter\(" + i + "\)." + index + "\(" + r + "\)=" + value ;
          }
        } 
        else {
          urlfilter += "&itemFilter\(" + i + "\)." + index + "=" + itemfilter[index];
        }
      }
    }
  }
}; 

buildURLArray(filterarray);

var url = "http://svcs.ebay.com/services/search/FindingService/v1";
    url += "?OPERATION-NAME=findItemsAdvanced";
    url += "&SERVICE-VERSION=1.13.0";
    url += "&SECURITY-APPNAME=Philipwa-6547-4a99-bb7f-42bceb8c89eb";
    url += "&GLOBAL-ID=EBAY-IE";
    url += "&RESPONSE-DATA-FORMAT=JSON";
    url += "&callback=_cb_findItemsAdvanced";
    url += "&REST-PAYLOAD";
    url += "&keywords="+barcode+"";
    url += "&outputSelector=CategoryHistogram";
    url += "&paginationInput.entriesPerPage=1";
    url += urlfilter;

var result = document.getElementById("result");
result.innerHTML = "<b>UPC:</b><i> " + barcode + "</i>";
// Submit the request 
s=document.createElement('script'); // create script element
s.src= url;
document.body.appendChild(s);
};
