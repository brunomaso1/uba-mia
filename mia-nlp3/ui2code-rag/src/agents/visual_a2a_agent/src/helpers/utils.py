def _hex_from_rgb(rgb):
    r, g, b = [int(x) for x in rgb]
    return "#{:02x}{:02x}{:02x}".format(r, g, b)

def _iou(a, b):
    # a,b: dicts {"x","y","w","h"}
    xa1, ya1, xa2, ya2 = a["x"], a["y"], a["x"]+a["w"], a["y"]+a["h"]
    xb1, yb1, xb2, yb2 = b["x"], b["y"], b["x"]+b["w"], b["y"]+b["h"]
    inter_w = max(0, min(xa2, xb2) - max(xa1, xb1))
    inter_h = max(0, min(ya2, yb2) - max(ya1, yb1))
    inter = inter_w * inter_h
    area_a = a["w"]*a["h"]; area_b = b["w"]*b["h"]
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0.0