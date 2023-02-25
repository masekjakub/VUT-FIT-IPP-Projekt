<?php
/**
 * @file Errors.php
 * @brief implements myError enum
 * @author Jakub Mašek
 * @date 2023-2-13
 */
enum myError:int{
    case E_OK = 0;
    case E_WRONGPARAM = 10;
    case E_WRONGOUTFILE = 12;
    case E_NOHEAD = 21;
    case E_WRONGOPCODE = 22;
    case E_OTHER = 23;
    case E_SEMANTIC = 52;
}
?>