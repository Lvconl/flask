/**
 * Created by lvconl on 18-2-12.
 */
function delete_blog() {
        var msg = "删除后不可恢复\n请确认删除";
        flag = confirm(meg);
        if (flag === true){
            window.event.returnValue = true;
        }else {
            window.event.returnValue = false;
        }
    }