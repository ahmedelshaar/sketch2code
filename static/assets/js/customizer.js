(function (jQuery) {
    "use strict";
    // data-mode="click" for using event
    // data-dark="false" for property
    
    const urlParams = new URLSearchParams(window.location.search);
    let storageDark = sessionStorage.getItem('dark')
    const myParam = urlParams.get('dark');
    
    if (myParam !== null) {
      console.log(myParam)
      if (myParam === 'true') {
        changeMode('true');
      } else {
        changeMode('false');
      }
    } else {
      if (storageDark === 'null') {
        changeMode('false');
      }
    }
    storageDark = sessionStorage.getItem('dark')
    if (storageDark !== 'null') {
      if (storageDark !== 'null') {
        changeMode(storageDark)
      }
    } else {
      if($('body').hasClass('dark')){
          changeMode('true');
      } else {
          changeMode('true');
      }
    }
    
    jQuery(document).on("change", '.change-mode input[type="checkbox"]' ,function (e) {
        const dark = $(this).attr('data-active');
        if (dark === 'true') {
            $(this).attr('data-active','false')
        } else {
            $(this).attr('data-active','true')
        }
        changeMode(dark)
    })
    function changeMode (dark) {
        const body = jQuery('body')
        updateLocalStorage(dark)
      if (dark === 'true') {
        $('[data-mode="toggle"]').find('i.a-right').removeClass('ri-sun-line');
        $('[data-mode="toggle"]').find('i.a-left').addClass('ri-moon-clear-line');
        $('#dark-mode').prop('checked', true).attr('data-active', 'false')
        body.addClass('dark')
        dark = true
      } else {
        $('[data-mode="toggle"]').find('i.a-left').removeClass('ri-moon-clear-line');
        $('[data-mode="toggle"]').find('i.a-right').addClass('ri-sun-line');
        $('#dark-mode').prop('checked', false).attr('data-active', 'true');
        body.removeClass('dark')
        dark = false
      }
        const event = new CustomEvent("ChangeColorMode", {detail: {dark: dark} });
        document.dispatchEvent(event);
    }
    function updateLocalStorage(dark) {
      sessionStorage.setItem('dark', dark)
    }
})(jQuery)
