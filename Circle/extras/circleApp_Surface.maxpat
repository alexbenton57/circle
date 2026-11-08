{
    "patcher": {
        "fileversion": 1,
        "appversion": {
            "major": 9,
            "minor": 1,
            "revision": 1,
            "architecture": "x64",
            "modernui": 1
        },
        "classnamespace": "box",
        "rect": [
            34.0,
            77.0,
            1213.0,
            642.0
        ],
        "boxes": [
            {
                "box": {
                    "automatic": 1,
                    "id": "obj-9",
                    "maxclass": "scope~",
                    "numinlets": 2,
                    "numoutlets": 0,
                    "patching_rect": [
                        283.0,
                        338.0,
                        130.0,
                        130.0
                    ]
                }
            },
            {
                "box": {
                    "id": "obj-15",
                    "linecount": 2,
                    "maxclass": "message",
                    "numinlets": 2,
                    "numoutlets": 1,
                    "outlettype": [
                        ""
                    ],
                    "patching_rect": [
                        518.2353157401085,
                        258.8235402107239,
                        182.94118410348892,
                        36.0
                    ],
                    "text": "0.562577 0.002153 0.043338 -0.529257 0.137324"
                }
            },
            {
                "box": {
                    "id": "obj-13",
                    "maxclass": "newobj",
                    "numinlets": 6,
                    "numoutlets": 1,
                    "outlettype": [
                        "signal"
                    ],
                    "patching_rect": [
                        199.46523481607437,
                        248.12833499908447,
                        323.6842074394226,
                        22.0
                    ],
                    "text": "biquad~ 0.326985 0.105079 0.023549 -0.706961 0.162574"
                }
            },
            {
                "box": {
                    "attr": "edit_mode",
                    "fontface": 0,
                    "fontname": "Arial",
                    "fontsize": 13.0,
                    "id": "obj-12",
                    "lock": 1,
                    "maxclass": "attrui",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "orientation": 1,
                    "outlettype": [
                        ""
                    ],
                    "parameter_enable": 0,
                    "patching_rect": [
                        346.71052300930023,
                        0.0,
                        83.0,
                        46.0
                    ],
                    "text_width": 83.0
                }
            },
            {
                "box": {
                    "fontface": 0,
                    "id": "obj-5",
                    "maxclass": "filtergraph~",
                    "nfilters": 1,
                    "numinlets": 8,
                    "numoutlets": 7,
                    "outlettype": [
                        "list",
                        "float",
                        "float",
                        "float",
                        "float",
                        "list",
                        "int"
                    ],
                    "parameter_enable": 0,
                    "patching_rect": [
                        438.81578528881073,
                        87.49999916553497,
                        256.0,
                        128.0
                    ],
                    "setfilter": [
                        0,
                        7,
                        1,
                        0,
                        0,
                        9286.3779296875,
                        0.3622760474681854,
                        0.7071067690849304,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0
                    ]
                }
            },
            {
                "box": {
                    "id": "obj-7",
                    "maxclass": "newobj",
                    "numinlets": 7,
                    "numoutlets": 3,
                    "outlettype": [
                        "multichannelsignal",
                        "",
                        ""
                    ],
                    "patching_rect": [
                        48.76190476190476,
                        127.1276586651802,
                        100.0,
                        22.0
                    ],
                    "text": "circleSynth_map"
                }
            },
            {
                "box": {
                    "id": "obj-8",
                    "linecount": 2,
                    "maxclass": "comment",
                    "numinlets": 1,
                    "numoutlets": 0,
                    "patching_rect": [
                        161.53846317529678,
                        33.33333367109299,
                        150.0,
                        34.0
                    ],
                    "text": "click if pad colours not locking"
                }
            },
            {
                "box": {
                    "id": "obj-6",
                    "maxclass": "button",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [
                        "bang"
                    ],
                    "parameter_enable": 0,
                    "patching_rect": [
                        132.4786338210106,
                        38.46153885126114,
                        24.0,
                        24.0
                    ]
                }
            },
            {
                "box": {
                    "id": "obj-4",
                    "maxclass": "newobj",
                    "numinlets": 2,
                    "numoutlets": 0,
                    "patching_rect": [
                        171.0,
                        371.0,
                        35.0,
                        22.0
                    ],
                    "text": "dac~"
                }
            },
            {
                "box": {
                    "id": "obj-3",
                    "maxclass": "newobj",
                    "numinlets": 3,
                    "numoutlets": 1,
                    "outlettype": [
                        "signal"
                    ],
                    "patching_rect": [
                        48.76190476190476,
                        174.46808385849,
                        110.0,
                        22.0
                    ],
                    "text": "circleSynth_engine"
                }
            },
            {
                "box": {
                    "id": "obj-2",
                    "maxclass": "newobj",
                    "numinlets": 3,
                    "numoutlets": 9,
                    "outlettype": [
                        "multichannelsignal",
                        "multichannelsignal",
                        "multichannelsignal",
                        "multichannelsignal",
                        "",
                        "",
                        "",
                        "multichannelsignal",
                        "multichannelsignal"
                    ],
                    "patching_rect": [
                        58.83333333333333,
                        80.0,
                        90.0,
                        22.0
                    ],
                    "text": "circleSynth_ctrl"
                }
            },
            {
                "box": {
                    "id": "obj-1",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 2,
                    "outlettype": [
                        "signal",
                        "signal"
                    ],
                    "patching_rect": [
                        59.0,
                        36.0,
                        35.0,
                        22.0
                    ],
                    "text": "adc~"
                }
            },
            {
                "box": {
                    "id": "obj-16",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [
                        ""
                    ],
                    "patching_rect": [
                        220.0,
                        35.0,
                        100.0,
                        22.0
                    ],
                    "text": "udpreceive 3334"
                }
            },
            {
                "box": {
                    "id": "obj-17",
                    "maxclass": "newobj",
                    "numinlets": 2,
                    "numoutlets": 2,
                    "outlettype": [
                        "",
                        ""
                    ],
                    "patching_rect": [
                        220.0,
                        62.0,
                        115.0,
                        22.0
                    ],
                    "text": "route /circle/note"
                }
            },
            {
                "box": {
                    "id": "obj-18",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "bang" ],
                    "patching_rect": [ 360.0, 35.0, 60.0, 22.0 ],
                    "text": "loadbang"
                }
            },
            {
                "box": {
                    "id": "obj-19",
                    "maxclass": "message",
                    "numinlets": 2,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 360.0, 65.0, 30.0, 22.0 ],
                    "text": "1"
                }
            },
            {
                "box": {
                    "id": "obj-20",
                    "maxclass": "newobj",
                    "numinlets": 2,
                    "numoutlets": 1,
                    "outlettype": [ "bang" ],
                    "patching_rect": [ 360.0, 95.0, 70.0, 22.0 ],
                    "text": "metro 500"
                }
            },
            {
                "box": {
                    "id": "obj-21",
                    "maxclass": "message",
                    "numinlets": 2,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 360.0, 125.0, 145.0, 22.0 ],
                    "text": "/circle/ready 1"
                }
            },
            {
                "box": {
                    "id": "obj-23",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 360.0, 185.0, 180.0, 22.0 ],
                    "text": "udpsend 127.0.0.1 3335"
                }
            },
            {
                "box": {
                    "id": "obj-24",
                    "maxclass": "newobj",
                    "numinlets": 2,
                    "numoutlets": 2,
                    "outlettype": [ "", "" ],
                    "patching_rect": [ 360.0, 245.0, 100.0, 22.0 ],
                    "text": "mc.snapshot~ 100"
                }
            },
            {
                "box": {
                    "id": "obj-25",
                    "maxclass": "newobj",
                    "numinlets": 2,
                    "numoutlets": 2,
                    "outlettype": [ "", "" ],
                    "patching_rect": [ 500.0, 245.0, 85.0, 22.0 ],
                    "text": "route voice"
                }
            },
            {
                "box": {
                    "id": "obj-26",
                    "maxclass": "newobj",
                    "numinlets": 2,
                    "numoutlets": 1,
                    "outlettype": [ "int" ],
                    "patching_rect": [ 600.0, 275.0, 35.0, 22.0 ],
                    "text": "int"
                }
            },
            {
                "box": {
                    "id": "obj-27",
                    "maxclass": "newobj",
                    "numinlets": 1,
                    "numoutlets": 2,
                    "outlettype": [ "bang", "float" ],
                    "patching_rect": [ 500.0, 275.0, 40.0, 22.0 ],
                    "text": "t b f"
                }
            },
            {
                "box": {
                    "id": "obj-28",
                    "maxclass": "newobj",
                    "numinlets": 2,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 600.0, 305.0, 60.0, 22.0 ],
                    "text": "pack i f"
                }
            },
            {
                "box": {
                    "id": "obj-29",
                    "maxclass": "newobj",
                    "numinlets": 2,
                    "numoutlets": 1,
                    "outlettype": [ "" ],
                    "patching_rect": [ 600.0, 335.0, 160.0, 22.0 ],
                    "text": "prepend /circle/feature"
                }
            }
        ],
        "lines": [
            {
                "patchline": {
                    "destination": [
                        "obj-2",
                        0
                    ],
                    "source": [
                        "obj-1",
                        0
                    ]
                }
            },
            {
                "patchline": {
                    "destination": [
                        "obj-5",
                        0
                    ],
                    "source": [
                        "obj-12",
                        0
                    ]
                }
            },
            {
                "patchline": {
                    "destination": [
                        "obj-4",
                        1
                    ],
                    "order": 1,
                    "source": [
                        "obj-13",
                        0
                    ]
                }
            },
            {
                "patchline": {
                    "destination": [
                        "obj-4",
                        0
                    ],
                    "order": 2,
                    "source": [
                        "obj-13",
                        0
                    ]
                }
            },
            {
                "patchline": {
                    "destination": [
                        "obj-9",
                        0
                    ],
                    "order": 0,
                    "source": [
                        "obj-13",
                        0
                    ]
                }
            },
            {
                "patchline": {
                    "destination": [
                        "obj-7",
                        6
                    ],
                    "source": [
                        "obj-2",
                        6
                    ]
                }
            },
            {
                "patchline": {
                    "destination": [
                        "obj-7",
                        5
                    ],
                    "source": [
                        "obj-2",
                        5
                    ]
                }
            },
            {
                "patchline": {
                    "destination": [
                        "obj-7",
                        4
                    ],
                    "source": [
                        "obj-2",
                        4
                    ]
                }
            },
            {
                "patchline": {
                    "destination": [
                        "obj-7",
                        3
                    ],
                    "source": [
                        "obj-2",
                        3
                    ]
                }
            },
            {
                "patchline": {
                    "destination": [
                        "obj-7",
                        2
                    ],
                    "source": [
                        "obj-2",
                        2
                    ]
                }
            },
            {
                "patchline": {
                    "destination": [
                        "obj-7",
                        1
                    ],
                    "source": [
                        "obj-2",
                        1
                    ]
                }
            },
            {
                "patchline": {
                    "destination": [
                        "obj-7",
                        0
                    ],
                    "source": [
                        "obj-2",
                        0
                    ]
                }
            },
            {
                "patchline": {
                    "destination": [
                        "obj-13",
                        0
                    ],
                    "source": [
                        "obj-3",
                        0
                    ]
                }
            },
            {
                "patchline": {
                    "destination": [
                        "obj-13",
                        0
                    ],
                    "order": 1,
                    "source": [
                        "obj-5",
                        0
                    ]
                }
            },
            {
                "patchline": {
                    "destination": [
                        "obj-15",
                        1
                    ],
                    "order": 0,
                    "source": [
                        "obj-5",
                        0
                    ]
                }
            },
            {
                "patchline": {
                    "destination": [
                        "obj-2",
                        1
                    ],
                    "source": [
                        "obj-6",
                        0
                    ]
                }
            },
            {
                "patchline": {
                    "destination": [
                        "obj-3",
                        2
                    ],
                    "source": [
                        "obj-7",
                        2
                    ]
                }
            },
            {
                "patchline": {
                    "destination": [
                        "obj-3",
                        1
                    ],
                    "source": [
                        "obj-7",
                        1
                    ]
                }
            },
            {
                "patchline": {
                    "destination": [
                        "obj-3",
                        0
                    ],
                    "source": [
                        "obj-7",
                        0
                    ]
                }
            },
            {
                "patchline": {
                    "source": [
                        "obj-16",
                        0
                    ],
                    "destination": [
                        "obj-17",
                        0
                    ]
                }
            },
            {
                "patchline": {
                    "source": [
                        "obj-17",
                        0
                    ],
                    "destination": [
                        "obj-2",
                        2
                    ]
                }
            },
            {
                "patchline": {
                    "source": [ "obj-18", 0 ],
                    "destination": [ "obj-19", 0 ]
                }
            },
            {
                "patchline": {
                    "source": [ "obj-19", 0 ],
                    "destination": [ "obj-20", 0 ]
                }
            },
            {
                "patchline": {
                    "source": [ "obj-20", 0 ],
                    "destination": [ "obj-21", 0 ]
                }
            },
            {
                "patchline": {
                    "source": [ "obj-21", 0 ],
                    "destination": [ "obj-23", 0 ]
                }
            },
            {
                "patchline": {
                    "source": [ "obj-2", 8 ],
                    "destination": [ "obj-24", 0 ]
                }
            },
            {
                "patchline": {
                    "source": [ "obj-24", 1 ],
                    "destination": [ "obj-25", 0 ]
                }
            },
            {
                "patchline": {
                    "source": [ "obj-25", 0 ],
                    "destination": [ "obj-26", 1 ]
                }
            },
            {
                "patchline": {
                    "source": [ "obj-24", 0 ],
                    "destination": [ "obj-27", 0 ]
                }
            },
            {
                "patchline": {
                    "source": [ "obj-27", 1 ],
                    "destination": [ "obj-28", 1 ]
                }
            },
            {
                "patchline": {
                    "source": [ "obj-27", 0 ],
                    "destination": [ "obj-26", 0 ]
                }
            },
            {
                "patchline": {
                    "source": [ "obj-26", 0 ],
                    "destination": [ "obj-28", 0 ]
                }
            },
            {
                "patchline": {
                    "source": [ "obj-28", 0 ],
                    "destination": [ "obj-29", 0 ]
                }
            },
            {
                "patchline": {
                    "source": [ "obj-29", 0 ],
                    "destination": [ "obj-23", 0 ]
                }
            }
        ],
        "autosave": 0
    }
}
