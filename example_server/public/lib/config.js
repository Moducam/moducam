fetch('/config')
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        document.getElementById('cameraPath').value = data.Camera.camera_path;
        document.getElementById('pixelThreshold').value = data.MotionSettings.pixel_threshold;
        document.getElementById('alarmThreshold').value = data.MotionSettings.alarm_threshold;
        document.getElementById('pixelStep').value = data.MotionSettings.pixel_step;
        document.getElementById('framesAfterAlarm').value = data.VideoSettings.frames_after_alarm;
        document.getElementById('bufferSize').value = data.VideoSettings.buffer_size;

        document.getElementById('rangeInput').value = data.MotionSettings.pixel_threshold
        document.getElementById('rangeInput2').value = data.MotionSettings.alarm_threshold;
        document.getElementById('rangeInput3').value = data.MotionSettings.pixel_step;
        document.getElementById('rangeInput4').value = data.VideoSettings.frames_after_alarm;
        document.getElementById('rangeInput5').value = data.VideoSettings.buffer_size;
        
        vertices = data.Zone.zone_points;
    });

document.getElementById("sendZonePoints").addEventListener('click', function() {
    var xhr = new XMLHttpRequest();
    xhr.open("POST", "/config", true);
    xhr.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
    xhr.onreadystatechange = function () {
        if (xhr.readyState === 4 && xhr.status === 200) {
            console.log(xhr.responseText);
        }
    };
    var data = {
        Camera: {
            camera_path: document.getElementById('cameraPath').value
        }, 
        MotionSettings: {
            pixel_threshold: document.getElementById('pixelThreshold').value,
            alarm_threshold: document.getElementById('alarmThreshold').value,
            pixel_step: document.getElementById('pixelStep').value
        }, 
        VideoSettings: {
            frames_after_alarm: document.getElementById('framesAfterAlarm').value,
            buffer_size: document.getElementById('bufferSize').value
        },
        Zone: {
            zone_points: vertices
        }
    }
    if (checkConfigs(data)) {
        console.log('configurations valid');
        document.getElementById('error').innerHTML = 'Saved'

        xhr.send(JSON.stringify(data));
    }
    else {
        console.log('cofigurations invalid');
        document.getElementById('error').innerHTML = 'Invalid configurations, cannot save'
    }
});

function checkConfigs(data) {
    for (const key in data) {
        for (const attr in data[key]) {
            if (data[key][attr] == '') {
                delete data[key][attr];
            }
        }
    }
    return true;
}