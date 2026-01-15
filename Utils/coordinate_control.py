def upper_orienation(lm):
    if lm[8].y < lm[6].y and lm[12].y > lm[10].y:
        return True
def left_orienation(lm):
    if lm[8].x < lm[6].x and lm[12].x > lm[10].x :
        return True


def right_orienation(lm):
    if lm[8].x > lm[6].x and lm[12].x < lm[10].x:
        return True

def erase_orienation(lm):
    if lm[8].y < lm[6].y and lm[12].y < lm[10].y:
        return True
def reset_orienation(lm):
     fist_closed = (
             lm[8].y > lm[6].y and
             lm[12].y > lm[10].y and
             lm[16].y > lm[14].y and
             lm[20].y > lm[18].y
     )
     if fist_closed:
         return True
