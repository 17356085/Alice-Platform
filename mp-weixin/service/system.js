"use strict";const e=require("../utils/http.js");exports.getMyDevices=function(){return e.http.get("/api/system/device/my-devices")};
