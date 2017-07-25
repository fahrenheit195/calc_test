package tests;

import calc.form1;
import org.testng.annotations.Test;

import static org.testng.AssertJUnit.assertEquals;

public class test {

    private calc.form1 calc = new form1();

    @Test
    public void testDiv() throws Exception{
        assertEquals(40f, calc.division(8f,0.2f));
    }

    @Test
    public  void testDiv2() {
        assertEquals(4f, calc.division(8f,2f));
    }
}
