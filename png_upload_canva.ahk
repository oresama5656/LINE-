; Canva PNG Upload Automation
; スリープ時間の設定
ShortSleep := 50  ; タブキー用のスリープ(ミリ秒)
LongSleep := 100  ; その他の操作用のスリープ(ミリ秒)

; ALT+1キーでスクリプト開始(タブ2～20回)
!1::
{
    ; 2回目から20回目まで繰り返し
    Loop, 19
    {
        CurrentTab := A_Index + 1  ; 現在のタブ回数(2~20)

        ; 下矢印
        Send, {Down}
        Sleep, %LongSleep%

        ; スペースキー
        Send, {Space}
        Sleep, %LongSleep%

        ; タブキーを現在の回数分押す
        Loop, %CurrentTab%
        {
            Send, {Tab}
            Sleep, %ShortSleep%
        }

        ; Enter
        Send, {Enter}
        Sleep, %LongSleep%
    }

    MsgBox, finish!
    Return
}

; ALT+2キーでスクリプト開始(タブ21～40回)
!2::
{
    ; 21回目から40回目まで繰り返し
    Loop, 20
    {
        CurrentTab := A_Index + 20  ; 現在のタブ回数(21~40)

        ; 下矢印
        Send, {Down}
        Sleep, %LongSleep%

        ; スペースキー
        Send, {Space}
        Sleep, %LongSleep%

        ; タブキーを現在の回数分押す
        Loop, %CurrentTab%
        {
            Send, {Tab}
            Sleep, %ShortSleep%
        }

        ; Enter
        Send, {Enter}
        Sleep, %LongSleep%
    }

    MsgBox, finish!
    Return
}

; Escキーで現在の処理を中断
Esc::Reload
